using System.Collections;
using System.Reflection;
using Microsoft.Extensions.Options;
using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public sealed class ReflectionOpennessRuntime(
    IOptions<TiaAgentOptions> options
) : IReflectionOpennessRuntime
{
    public OpennessDiagnosticsResponse GetDiagnostics()
    {
        var config = options.Value;
        var assemblyDirectoryExists = Directory.Exists(config.SiemensAssemblyDirectory);
        var engineeringAssemblyPath = Path.Combine(
            config.SiemensAssemblyDirectory,
            "Siemens.Engineering.dll"
        );
        var engineeringAssemblyExists = File.Exists(engineeringAssemblyPath);
        var defaultProjectPathExists =
            !string.IsNullOrWhiteSpace(config.DefaultProjectPath)
            && File.Exists(config.DefaultProjectPath);

        var notes = new List<string>();

        if (!assemblyDirectoryExists)
        {
            notes.Add("Directory Siemens PublicAPI non trovata.");
        }

        if (!engineeringAssemblyExists)
        {
            notes.Add("Assembly Siemens.Engineering.dll non trovato.");
        }

        if (!defaultProjectPathExists)
        {
            notes.Add("ProjectPath di default non trovato o non configurato.");
        }

        if (string.Equals(config.OpennessMode, "real", StringComparison.OrdinalIgnoreCase))
        {
            notes.Add(
                "Modalita' real attiva: il runtime tenta apertura progetto, compile e import/export via reflection."
            );
        }
        else
        {
            notes.Add("Modalita' stub attiva: nessuna chiamata reale a TIA Portal verra' eseguita.");
        }

        return new OpennessDiagnosticsResponse(
            Service: "tia-windows-agent",
            Mode: config.OpennessMode,
            TiaPortalVersion: config.TiaPortalVersion,
            SiemensAssemblyDirectory: config.SiemensAssemblyDirectory,
            SiemensAssemblyDirectoryExists: assemblyDirectoryExists,
            SiemensEngineeringAssemblyPath: engineeringAssemblyPath,
            SiemensEngineeringAssemblyExists: engineeringAssemblyExists,
            DefaultProjectPath: config.DefaultProjectPath,
            DefaultProjectPathExists: defaultProjectPathExists,
            LaunchUi: config.LaunchUi,
            Notes: notes
        );
    }

    public async Task<OpennessExecutionResult> ExecuteAsync(
        TiaJob job,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var config = options.Value;
        ValidateJob(job);

        if (!string.Equals(config.OpennessMode, "real", StringComparison.OrdinalIgnoreCase))
        {
            await Task.Delay(150, cancellationToken);
            return new OpennessExecutionResult(
                "completed",
                $"Job {job.Operation} validato in modalita' stub. Nessuna chiamata reale a TIA."
            );
        }

        var diagnostics = GetDiagnostics();

        if (!diagnostics.SiemensAssemblyDirectoryExists || !diagnostics.SiemensEngineeringAssemblyExists)
        {
            return new OpennessExecutionResult(
                "blocked",
                "Ambiente Openness non pronto: verifica SiemensAssemblyDirectory e Siemens.Engineering.dll."
            );
        }

        return await ExecuteRealAsync(job, diagnostics.SiemensEngineeringAssemblyPath, config, cancellationToken);
    }

    private static void ValidateJob(TiaJob job)
    {
        if (string.IsNullOrWhiteSpace(job.ArtifactPath))
        {
            throw new InvalidOperationException("ArtifactPath obbligatorio.");
        }

        if (job.Operation is "import" && !File.Exists(job.ArtifactPath))
        {
            throw new FileNotFoundException("ArtifactPath non trovato.", job.ArtifactPath);
        }

        if (job.Operation is "compile" or "import" or "export")
        {
            if (string.IsNullOrWhiteSpace(job.ProjectPath))
            {
                throw new InvalidOperationException("ProjectPath obbligatorio per il job richiesto.");
            }

            if (!File.Exists(job.ProjectPath))
            {
                throw new FileNotFoundException("ProjectPath non trovato.", job.ProjectPath);
            }
        }
    }

    private static async Task<OpennessExecutionResult> ExecuteRealAsync(
        TiaJob job,
        string engineeringAssemblyPath,
        TiaAgentOptions config,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var assembly = Assembly.LoadFrom(engineeringAssemblyPath);
        var tiaPortal = CreateTiaPortalInstance(assembly, config);

        try
        {
            var project = OpenProject(tiaPortal, job.ProjectPath!);

            try
            {
                return job.Operation switch
                {
                    "compile" => await CompileAsync(assembly, project, cancellationToken),
                    "import" => await ImportAsync(project, job, cancellationToken),
                    "export" => await ExportAsync(project, job, cancellationToken),
                    _ => throw new InvalidOperationException($"Operazione non supportata: {job.Operation}"),
                };
            }
            finally
            {
                TryDispose(project);
            }
        }
        finally
        {
            TryDispose(tiaPortal);
        }
    }

    private static object CreateTiaPortalInstance(Assembly assembly, TiaAgentOptions config)
    {
        var tiaPortalType = assembly.GetType("Siemens.Engineering.TiaPortal")
            ?? throw new InvalidOperationException("Tipo Siemens.Engineering.TiaPortal non trovato.");
        var tiaPortalModeType = assembly.GetType("Siemens.Engineering.TiaPortalMode")
            ?? throw new InvalidOperationException("Tipo Siemens.Engineering.TiaPortalMode non trovato.");

        var desiredModeName = config.LaunchUi ? "WithUserInterface" : "WithoutUserInterface";
        var mode = Enum.Parse(tiaPortalModeType, desiredModeName, ignoreCase: false);

        return Activator.CreateInstance(tiaPortalType, mode)
            ?? throw new InvalidOperationException("Impossibile creare una istanza TiaPortal via reflection.");
    }

    private static object OpenProject(object tiaPortal, string projectPath)
    {
        var projects = GetPropertyValue(tiaPortal, "Projects")
            ?? throw new InvalidOperationException("Collection Projects non trovata su TiaPortal.");

        var openMethod = projects.GetType()
            .GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .FirstOrDefault(method =>
                method.Name == "Open"
                && method.GetParameters().Length >= 1
                && method.GetParameters()[0].ParameterType == typeof(FileInfo)
            )
            ?? throw new InvalidOperationException("Metodo Projects.Open(FileInfo) non trovato.");

        return openMethod.Invoke(projects, BuildFileArguments(openMethod, new FileInfo(projectPath)))
            ?? throw new InvalidOperationException("Projects.Open ha restituito null.");
    }

    private static async Task<OpennessExecutionResult> CompileAsync(
        Assembly assembly,
        object project,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var compilableType = assembly.GetType("Siemens.Engineering.Compiler.ICompilable")
            ?? throw new InvalidOperationException("Tipo Siemens.Engineering.Compiler.ICompilable non trovato.");

        var candidates = new List<object> { project };
        var plcSoftware = TryFindFirstPlcSoftware(project);
        if (plcSoftware is not null)
        {
            candidates.Add(plcSoftware);
        }

        foreach (var candidate in candidates)
        {
            var compilable = TryGetService(candidate, compilableType);
            if (compilable is null)
            {
                continue;
            }

            var compileMethod = compilable.GetType()
                .GetMethods(BindingFlags.Instance | BindingFlags.Public)
                .FirstOrDefault(method => method.Name == "Compile" && method.GetParameters().Length == 0);

            if (compileMethod is null)
            {
                continue;
            }

            var result = compileMethod.Invoke(compilable, Array.Empty<object?>());
            var summary = DescribeCompilationResult(result);
            await Task.CompletedTask;

            return new OpennessExecutionResult("completed", $"Compile completata. {summary}");
        }

        return new OpennessExecutionResult(
            "blocked",
            "Nessun servizio ICompilable trovato su project o PlcSoftware."
        );
    }

    private static async Task<OpennessExecutionResult> ImportAsync(
        object project,
        TiaJob job,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var plcSoftware = TryFindFirstPlcSoftware(project)
            ?? throw new InvalidOperationException("Nessun PlcSoftware trovato nel progetto.");

        var rootBlockGroup = GetPropertyValue(plcSoftware, "BlockGroup")
            ?? throw new InvalidOperationException("BlockGroup non trovato su PlcSoftware.");

        var targetGroup = ResolveBlockGroup(rootBlockGroup, job.TargetPath);
        var importTarget = GetPropertyValue(targetGroup, "Blocks") ?? targetGroup;
        var importFile = new FileInfo(job.ArtifactPath);

        if (!TryInvokeImport(importTarget, importFile, out var importDescription))
        {
            var available = DescribePublicMethods(importTarget, "Import");
            return new OpennessExecutionResult(
                "blocked",
                $"Import non riuscito: nessuna firma Import compatibile trovata su {importTarget.GetType().FullName}. Metodi osservati: {available}"
            );
        }

        if (job.SaveProject)
        {
            TrySaveProject(project);
        }

        await Task.CompletedTask;
        return new OpennessExecutionResult(
            "completed",
            $"Import completato in '{DescribeObject(targetGroup)}'. {importDescription}"
        );
    }

    private static async Task<OpennessExecutionResult> ExportAsync(
        object project,
        TiaJob job,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var plcSoftware = TryFindFirstPlcSoftware(project)
            ?? throw new InvalidOperationException("Nessun PlcSoftware trovato nel progetto.");

        var rootBlockGroup = GetPropertyValue(plcSoftware, "BlockGroup")
            ?? throw new InvalidOperationException("BlockGroup non trovato su PlcSoftware.");

        var blockName = !string.IsNullOrWhiteSpace(job.TargetName)
            ? job.TargetName
            : Path.GetFileNameWithoutExtension(job.ArtifactPath);

        var block = FindBlockByName(rootBlockGroup, blockName!)
            ?? throw new InvalidOperationException(
                $"Blocco '{blockName}' non trovato nel progetto. Specifica TargetName se necessario."
            );

        var exportFile = new FileInfo(job.ArtifactPath);
        Directory.CreateDirectory(
            exportFile.DirectoryName
                ?? throw new InvalidOperationException("Directory export non valida.")
        );

        if (!TryInvokeExport(block, exportFile, out var exportDescription))
        {
            var available = DescribePublicMethods(block, "Export");
            return new OpennessExecutionResult(
                "blocked",
                $"Export non riuscito: nessuna firma Export compatibile trovata su {block.GetType().FullName}. Metodi osservati: {available}"
            );
        }

        if (job.SaveProject)
        {
            TrySaveProject(project);
        }

        await Task.CompletedTask;
        return new OpennessExecutionResult(
            "completed",
            $"Export completato dal blocco '{blockName}' verso '{job.ArtifactPath}'. {exportDescription}"
        );
    }

    private static object? TryFindFirstPlcSoftware(object project)
    {
        foreach (var device in EnumerateObjects(GetPropertyValue(project, "Devices")))
        {
            var software = FindPlcSoftwareRecursive(device);
            if (software is not null)
            {
                return software;
            }
        }

        return null;
    }

    private static object? FindPlcSoftwareRecursive(object node)
    {
        var nodeTypeName = node.GetType().FullName ?? string.Empty;
        if (nodeTypeName.Contains("PlcSoftware", StringComparison.OrdinalIgnoreCase))
        {
            return node;
        }

        var softwareContainer = TryGetServiceByTypeName(
            node,
            "Siemens.Engineering.HW.Features.SoftwareContainer"
        );
        var software = softwareContainer is null ? null : GetPropertyValue(softwareContainer, "Software");
        if (software?.GetType().FullName?.Contains("PlcSoftware", StringComparison.OrdinalIgnoreCase) == true)
        {
            return software;
        }

        foreach (var child in EnumerateObjects(GetPropertyValue(node, "DeviceItems")))
        {
            var result = FindPlcSoftwareRecursive(child);
            if (result is not null)
            {
                return result;
            }
        }

        return null;
    }

    private static object ResolveBlockGroup(object rootBlockGroup, string? targetPath)
    {
        if (string.IsNullOrWhiteSpace(targetPath))
        {
            return rootBlockGroup;
        }

        var current = rootBlockGroup;
        var parts = targetPath.Split(
            '/',
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries
        );

        foreach (var part in parts)
        {
            current = FindChildGroupByName(current, part)
                ?? throw new InvalidOperationException(
                    $"BlockGroup '{part}' non trovato nel path '{targetPath}'."
                );
        }

        return current;
    }

    private static object? FindChildGroupByName(object blockGroup, string name)
    {
        foreach (var collectionName in new[] { "Groups", "GroupComposition", "BlockGroups" })
        {
            foreach (var item in EnumerateObjects(GetPropertyValue(blockGroup, collectionName)))
            {
                if (string.Equals(DescribeObject(item), name, StringComparison.OrdinalIgnoreCase))
                {
                    return item;
                }
            }
        }

        return null;
    }

    private static object? FindBlockByName(object blockGroup, string blockName)
    {
        foreach (var block in EnumerateObjects(GetPropertyValue(blockGroup, "Blocks")))
        {
            if (string.Equals(DescribeObject(block), blockName, StringComparison.OrdinalIgnoreCase))
            {
                return block;
            }
        }

        foreach (var childGroup in EnumerateObjects(GetPropertyValue(blockGroup, "Groups")))
        {
            var result = FindBlockByName(childGroup, blockName);
            if (result is not null)
            {
                return result;
            }
        }

        return null;
    }

    private static bool TryInvokeImport(object target, FileInfo fileInfo, out string description)
    {
        foreach (var method in target.GetType().GetMethods(BindingFlags.Instance | BindingFlags.Public))
        {
            if (!string.Equals(method.Name, "Import", StringComparison.Ordinal))
            {
                continue;
            }

            if (!TryBuildFileInvocationArguments(method, fileInfo, out var args))
            {
                continue;
            }

            try
            {
                method.Invoke(target, args);
                description = $"Metodo {method.Name} invocato su {target.GetType().Name}.";
                return true;
            }
            catch
            {
            }
        }

        description = "Nessuna overload Import compatibile invocata.";
        return false;
    }

    private static bool TryInvokeExport(object target, FileInfo fileInfo, out string description)
    {
        foreach (var method in target.GetType().GetMethods(BindingFlags.Instance | BindingFlags.Public))
        {
            if (!string.Equals(method.Name, "Export", StringComparison.Ordinal))
            {
                continue;
            }

            if (!TryBuildFileInvocationArguments(method, fileInfo, out var args))
            {
                continue;
            }

            try
            {
                method.Invoke(target, args);
                description = $"Metodo {method.Name} invocato su {target.GetType().Name}.";
                return true;
            }
            catch
            {
            }
        }

        description = "Nessuna overload Export compatibile invocata.";
        return false;
    }

    private static bool TryBuildFileInvocationArguments(
        MethodInfo method,
        FileInfo fileInfo,
        out object?[] args
    )
    {
        var parameters = method.GetParameters();
        args = new object?[parameters.Length];

        if (parameters.Length == 0 || parameters[0].ParameterType != typeof(FileInfo))
        {
            return false;
        }

        args[0] = fileInfo;

        for (var index = 1; index < parameters.Length; index++)
        {
            var parameter = parameters[index];
            if (parameter.HasDefaultValue)
            {
                args[index] = parameter.DefaultValue;
                continue;
            }

            if (parameter.ParameterType == typeof(bool))
            {
                args[index] = true;
                continue;
            }

            if (parameter.ParameterType.IsEnum)
            {
                args[index] = GetPreferredEnumValue(parameter.ParameterType);
                continue;
            }

            return false;
        }

        return true;
    }

    private static object?[] BuildFileArguments(MethodInfo method, FileInfo fileInfo)
    {
        if (!TryBuildFileInvocationArguments(method, fileInfo, out var args))
        {
            throw new InvalidOperationException($"Firma non supportata per il metodo {method.Name}.");
        }

        return args;
    }

    private static object GetPreferredEnumValue(Type enumType)
    {
        var names = Enum.GetNames(enumType);
        foreach (var preferred in new[] { "Override", "Replace", "None", "Default" })
        {
            var match = names.FirstOrDefault(
                name => string.Equals(name, preferred, StringComparison.OrdinalIgnoreCase)
            );
            if (match is not null)
            {
                return Enum.Parse(enumType, match);
            }
        }

        return Enum.GetValues(enumType).GetValue(0)
            ?? throw new InvalidOperationException($"Enum vuoto non supportato: {enumType.FullName}");
    }

    private static void TrySaveProject(object project)
    {
        var saveMethod = project.GetType()
            .GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .FirstOrDefault(method => method.Name == "Save" && method.GetParameters().Length == 0);

        saveMethod?.Invoke(project, Array.Empty<object?>());
    }

    private static object? TryGetService(object target, Type serviceType)
    {
        var methods = target.GetType()
            .GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .Where(method => method.Name == "GetService")
            .ToList();

        foreach (var method in methods.Where(method => !method.IsGenericMethodDefinition))
        {
            var parameters = method.GetParameters();
            if (parameters.Length == 1 && parameters[0].ParameterType == typeof(Type))
            {
                try
                {
                    return method.Invoke(target, new object?[] { serviceType });
                }
                catch
                {
                }
            }
        }

        foreach (var method in methods.Where(method => method.IsGenericMethodDefinition))
        {
            try
            {
                return method.MakeGenericMethod(serviceType).Invoke(target, Array.Empty<object?>());
            }
            catch
            {
            }
        }

        return null;
    }

    private static object? TryGetServiceByTypeName(object target, string typeName)
    {
        var serviceType = target.GetType().Assembly.GetType(typeName);
        return serviceType is null ? null : TryGetService(target, serviceType);
    }

    private static object? GetPropertyValue(object target, string propertyName)
    {
        return target.GetType()
            .GetProperty(propertyName, BindingFlags.Instance | BindingFlags.Public)
            ?.GetValue(target);
    }

    private static IEnumerable<object> EnumerateObjects(object? sequence)
    {
        if (sequence is null)
        {
            yield break;
        }

        if (sequence is IEnumerable enumerable)
        {
            foreach (var item in enumerable)
            {
                if (item is not null)
                {
                    yield return item;
                }
            }
        }
    }

    private static string DescribeCompilationResult(object? result)
    {
        if (result is null)
        {
            return "Nessun risultato dettagliato restituito dal compilatore.";
        }

        var state = GetPropertyValue(result, "State")?.ToString();
        var messages = GetPropertyValue(result, "Messages");
        var messageCount = EnumerateObjects(messages).Count();

        return $"State={state ?? "n/a"}, Messages={messageCount}.";
    }

    private static string DescribeObject(object target)
    {
        return GetPropertyValue(target, "Name")?.ToString()
            ?? GetPropertyValue(target, "DisplayName")?.ToString()
            ?? target.ToString()
            ?? target.GetType().Name;
    }

    private static string DescribePublicMethods(object target, string methodName)
    {
        var methods = target.GetType()
            .GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .Where(method => method.Name == methodName)
            .Select(method =>
            {
                var parameters = string.Join(
                    ", ",
                    method.GetParameters().Select(parameter => parameter.ParameterType.Name)
                );
                return $"{method.Name}({parameters})";
            })
            .Distinct()
            .ToList();

        return methods.Count == 0 ? "nessuno" : string.Join("; ", methods);
    }

    private static void TryDispose(object? target)
    {
        if (target is IDisposable disposable)
        {
            disposable.Dispose();
        }
    }
}
