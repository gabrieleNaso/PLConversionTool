using System.Collections;
using System.Reflection;
using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public sealed class ReflectionOpennessRuntime(
    TiaAgentOptions options
) : IReflectionOpennessRuntime
{
    public OpennessDiagnosticsResponse GetDiagnostics()
    {
        var config = options;
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

        var config = options;
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
                    "compile" => await CompileAsync(assembly, project, job, cancellationToken),
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
        TiaJob job,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var compilableType = assembly.GetType("Siemens.Engineering.Compiler.ICompilable")
            ?? throw new InvalidOperationException("Tipo Siemens.Engineering.Compiler.ICompilable non trovato.");

        var plcSoftware = TryFindFirstPlcSoftware(project);
        var candidates = new List<object>();
        if (plcSoftware is not null)
        {
            candidates.Add(plcSoftware);
        }
        candidates.Add(project);

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
            var summary = DescribeCompilationResult(result, out var compileSucceeded);
            await Task.CompletedTask;

            if (!compileSucceeded)
            {
                return new OpennessExecutionResult(
                    "blocked",
                    $"Compile eseguita ma TIA ha restituito un esito non valido su '{DescribeObject(candidate)}'. {summary}"
                );
            }

            if (job.SaveProject)
            {
                TrySaveProject(project);
            }

            return new OpennessExecutionResult(
                "completed",
                $"Compile completata su '{DescribeObject(candidate)}'. {summary}"
            );
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
                $"Import non riuscito su {importTarget.GetType().FullName}. {importDescription} Metodi osservati: {available}"
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

        var compileBeforeExportResult = await CompileAsync(
            project.GetType().Assembly,
            project,
            job with { Operation = "compile", SaveProject = true },
            cancellationToken
        );

        if (!string.Equals(compileBeforeExportResult.Status, "completed", StringComparison.OrdinalIgnoreCase))
        {
            return new OpennessExecutionResult(
                "blocked",
                $"Export annullato: compile automatica preliminare non riuscita. {compileBeforeExportResult.Detail}"
            );
        }

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
                $"Export non riuscito su {block.GetType().FullName}. {exportDescription} Metodi osservati: {available}"
            );
        }

        if (job.SaveProject)
        {
            TrySaveProject(project);
        }

        await Task.CompletedTask;
        return new OpennessExecutionResult(
            "completed",
            $"Compile automatica preliminare riuscita. Export completato dal blocco '{blockName}' verso '{job.ArtifactPath}'. {exportDescription}"
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
        if (ContainsIgnoreCase(nodeTypeName, "PlcSoftware"))
        {
            return node;
        }

        var softwareContainer = TryGetServiceByTypeName(
            node,
            "Siemens.Engineering.HW.Features.SoftwareContainer"
        );
        var software = softwareContainer is null ? null : GetPropertyValue(softwareContainer, "Software");
        if (software != null && ContainsIgnoreCase(software.GetType().FullName, "PlcSoftware"))
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
        var parts = targetPath
            .Split(new[] { '/' }, StringSplitOptions.RemoveEmptyEntries)
            .Select(part => part.Trim())
            .Where(part => part.Length > 0)
            .ToArray();

        if (parts.Length == 1 && IsRootBlockGroupName(rootBlockGroup, parts[0]))
        {
            return rootBlockGroup;
        }

        foreach (var part in parts)
        {
            if (IsRootBlockGroupName(current, part))
            {
                continue;
            }

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
        string lastError = null;
        var diagnostics = new List<string>();

        foreach (var method in target.GetType().GetMethods(BindingFlags.Instance | BindingFlags.Public))
        {
            if (!string.Equals(method.Name, "Import", StringComparison.Ordinal))
            {
                continue;
            }

            object?[][] allArgs;
            string buildReason;
            if (!TryBuildFileInvocationArguments(method, fileInfo, out allArgs, out buildReason))
            {
                diagnostics.Add($"{DescribeMethod(method)} -> skipped: {buildReason}");
                continue;
            }

            foreach (var args in allArgs)
            {
                try
                {
                    method.Invoke(target, args);
                    description = $"Metodo {method.Name} invocato su {target.GetType().Name} con argomenti compatibili.";
                    return true;
                }
                catch (Exception ex)
                {
                    lastError = BuildInvocationErrorDetail(ex);
                    diagnostics.Add($"{DescribeMethod(method)} -> invoke failed: {lastError}");
                }
            }
        }

        description = BuildImportExportFailureDescription(
            baseMessage: "Nessuna overload Import compatibile invocata.",
            lastError: lastError,
            diagnostics: diagnostics
        );
        return false;
    }

    private static bool TryInvokeExport(object target, FileInfo fileInfo, out string description)
    {
        string lastError = null;
        var diagnostics = new List<string>();

        foreach (var method in target.GetType().GetMethods(BindingFlags.Instance | BindingFlags.Public))
        {
            if (!string.Equals(method.Name, "Export", StringComparison.Ordinal))
            {
                continue;
            }

            object?[][] allArgs;
            string buildReason;
            if (!TryBuildFileInvocationArguments(method, fileInfo, out allArgs, out buildReason))
            {
                diagnostics.Add($"{DescribeMethod(method)} -> skipped: {buildReason}");
                continue;
            }

            foreach (var args in allArgs)
            {
                try
                {
                    method.Invoke(target, args);
                    description = $"Metodo {method.Name} invocato su {target.GetType().Name} con argomenti compatibili.";
                    return true;
                }
                catch (Exception ex)
                {
                    lastError = BuildInvocationErrorDetail(ex);
                    diagnostics.Add($"{DescribeMethod(method)} -> invoke failed: {lastError}");
                }
            }
        }

        description = BuildImportExportFailureDescription(
            baseMessage: "Nessuna overload Export compatibile invocata.",
            lastError: lastError,
            diagnostics: diagnostics
        );
        return false;
    }

    private static bool TryBuildFileInvocationArguments(
        MethodInfo method,
        FileInfo fileInfo,
        out object?[][] argsSets,
        out string reason
    )
    {
        var parameters = method.GetParameters();
        argsSets = null;
        reason = null;

        if (parameters.Length == 0 || parameters[0].ParameterType != typeof(FileInfo))
        {
            reason = "primo parametro diverso da FileInfo o firma vuota";
            return false;
        }

        var candidateValues = new List<object>[parameters.Length];
        candidateValues[0] = new List<object> { fileInfo };

        for (var index = 1; index < parameters.Length; index++)
        {
            var parameter = parameters[index];
            if (parameter.HasDefaultValue)
            {
                candidateValues[index] = new List<object> { parameter.DefaultValue };
                continue;
            }

            if (parameter.ParameterType == typeof(bool))
            {
                candidateValues[index] = new List<object> { true, false };
                continue;
            }

            if (parameter.ParameterType.IsEnum)
            {
                candidateValues[index] = GetEnumCandidates(parameter.ParameterType).Cast<object>().ToList();
                continue;
            }

            if (TryGetStaticOptionCandidates(parameter.ParameterType, out var staticCandidates))
            {
                candidateValues[index] = staticCandidates.ToList();
                continue;
            }

            if (TryCreateOptionCandidates(parameter.ParameterType, out var optionCandidates))
            {
                candidateValues[index] = optionCandidates.Cast<object>().ToList();
                continue;
            }

            if (!parameter.ParameterType.IsValueType)
            {
                candidateValues[index] = new List<object> { null };
                continue;
            }

            reason = $"parametro non supportato: {parameter.Name} ({parameter.ParameterType.FullName})";
            return false;
        }

        argsSets = BuildCartesianProduct(candidateValues);
        reason = $"argomenti costruiti: {argsSets.Length} combinazioni";
        return true;
    }

    private static object?[] BuildFileArguments(MethodInfo method, FileInfo fileInfo)
    {
        object?[][] argsSets;
        string reason;
        if (!TryBuildFileInvocationArguments(method, fileInfo, out argsSets, out reason) || argsSets.Length == 0)
        {
            throw new InvalidOperationException($"Firma non supportata per il metodo {method.Name}. {reason}");
        }

        return argsSets[0];
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

    private static Array GetEnumCandidates(Type enumType)
    {
        var values = Enum.GetValues(enumType).Cast<object>().ToList();
        if (values.Count == 0)
        {
            throw new InvalidOperationException($"Enum vuoto non supportato: {enumType.FullName}");
        }

        if (values.Count == 1)
        {
            var single = Array.CreateInstance(enumType, 1);
            single.SetValue(values[0], 0);
            return single;
        }

        var preferred = GetPreferredEnumValue(enumType);
        var ordered = new List<object> { preferred };
        ordered.AddRange(values.Where(value => !Equals(value, preferred)));

        var result = Array.CreateInstance(enumType, ordered.Count);
        for (var index = 0; index < ordered.Count; index++)
        {
            result.SetValue(ordered[index], index);
        }

        return result;
    }

    private static object?[][] BuildCartesianProduct(IReadOnlyList<List<object>> values)
    {
        var results = new List<object?[]>();
        var current = new object?[values.Count];

        void Recurse(int index)
        {
            if (index == values.Count)
            {
                results.Add((object?[])current.Clone());
                return;
            }

            foreach (var value in values[index])
            {
                current[index] = value;
                Recurse(index + 1);
            }
        }

        Recurse(0);
        return results.ToArray();
    }

    private static string BuildInvocationErrorDetail(Exception exception)
    {
        var friendly = TryBuildFriendlyEngineeringError(exception);
        if (!string.IsNullOrWhiteSpace(friendly))
        {
            return friendly;
        }

        var chain = new List<string>();
        var current = exception;

        while (current != null)
        {
            chain.Add($"{current.GetType().FullName}: {current.Message}");
            current = current.InnerException;
        }

        return string.Join(" | INNER -> ", chain);
    }

    private static string TryBuildFriendlyEngineeringError(Exception exception)
    {
        var current = exception;
        while (current != null)
        {
            var typeName = current.GetType().FullName ?? string.Empty;
            if (typeName.IndexOf("LicenseNotFoundException", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                return BuildLicenseErrorMessage(current.Message);
            }

            current = current.InnerException;
        }

        return null;
    }

    private static string BuildLicenseErrorMessage(string message)
    {
        var compact = NormalizeWhitespace(message);

        if (compact.IndexOf("STEP 7 Professional", StringComparison.OrdinalIgnoreCase) >= 0)
        {
            return "Licenza mancante: TIA Openness riesce a eseguire l'import ma TIA rifiuta la creazione del blocco per assenza della licenza 'STEP 7 Professional'.";
        }

        return $"Licenza mancante rilevata da TIA Openness: {compact}";
    }

    private static string NormalizeWhitespace(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return string.Empty;
        }

        var parts = text
            .Split(new[] { ' ', '\r', '\n', '\t' }, StringSplitOptions.RemoveEmptyEntries);

        return string.Join(" ", parts);
    }

    private static string BuildImportExportFailureDescription(
        string baseMessage,
        string lastError,
        IReadOnlyList<string> diagnostics
    )
    {
        var parts = new List<string> { baseMessage };

        if (!string.IsNullOrWhiteSpace(lastError))
        {
            parts.Add($"Ultimo errore: {lastError}");
        }

        if (diagnostics != null && diagnostics.Count > 0)
        {
            parts.Add($"Diagnostica overload: {string.Join(" || ", diagnostics)}");
        }

        return string.Join(" ", parts);
    }

    private static string DescribeMethod(MethodInfo method)
    {
        var parameters = string.Join(
            ", ",
            method.GetParameters().Select(parameter => $"{parameter.ParameterType.Name} {parameter.Name}")
        );

        return $"{method.Name}({parameters})";
    }

    private static bool TryCreateOptionCandidates(Type parameterType, out object[] candidates)
    {
        candidates = null;

        if (parameterType == typeof(string))
        {
            return false;
        }

        if (parameterType.IsAbstract || parameterType.IsInterface)
        {
            return false;
        }

        var instance = TryCreateOptionInstance(parameterType);
        var configuredInstance = TryCreateOptionInstance(parameterType);

        if (instance == null || configuredInstance == null)
        {
            return false;
        }

        ConfigureOptionVariant(configuredInstance, setBooleansToTrue: true);

        candidates = new[] { instance, configuredInstance };
        return true;
    }

    private static bool TryGetStaticOptionCandidates(Type parameterType, out List<object> candidates)
    {
        candidates = new List<object>();

        foreach (var field in parameterType.GetFields(BindingFlags.Public | BindingFlags.Static))
        {
            if (parameterType.IsAssignableFrom(field.FieldType))
            {
                var value = field.GetValue(null);
                if (value != null)
                {
                    candidates.Add(value);
                }
            }
        }

        foreach (var property in parameterType.GetProperties(BindingFlags.Public | BindingFlags.Static))
        {
            if (property.CanRead && parameterType.IsAssignableFrom(property.PropertyType))
            {
                var value = property.GetValue(null, null);
                if (value != null)
                {
                    candidates.Add(value);
                }
            }
        }

        if (candidates.Count == 0)
        {
            return false;
        }

        var preferredNames = new[]
        {
            "Override",
            "Replace",
            "None",
            "Default",
            "IgnoreMissingReferencedObjects",
            "IgnoreMissingReferencedObject",
            "IgnoreStructuralChanges",
            "IgnoreUnitAttributes",
        };

        candidates = candidates
            .GroupBy(item => item.ToString())
            .Select(group => group.First())
            .OrderBy(item =>
            {
                var name = item.ToString() ?? string.Empty;
                var index = Array.FindIndex(
                    preferredNames,
                    preferred => string.Equals(preferred, name, StringComparison.OrdinalIgnoreCase)
                );
                return index < 0 ? int.MaxValue : index;
            })
            .ToList();

        return candidates.Count > 0;
    }

    private static object TryCreateOptionInstance(Type parameterType)
    {
        try
        {
            return Activator.CreateInstance(parameterType, true);
        }
        catch
        {
        }

        if (parameterType.IsValueType)
        {
            try
            {
                return Activator.CreateInstance(parameterType);
            }
            catch
            {
            }
        }

        try
        {
            return FormatterServices.GetUninitializedObject(parameterType);
        }
        catch
        {
        }

        return null;
    }

    private static void ConfigureOptionVariant(object instance, bool setBooleansToTrue)
    {
        var properties = instance.GetType()
            .GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(property => property.CanWrite)
            .ToList();

        foreach (var property in properties)
        {
            try
            {
                if (property.PropertyType == typeof(bool))
                {
                    property.SetValue(instance, setBooleansToTrue);
                    continue;
                }

                if (property.PropertyType.IsEnum)
                {
                    property.SetValue(instance, GetPreferredEnumValue(property.PropertyType));
                }
            }
            catch
            {
                // Best effort only: leave default value if a property cannot be assigned.
            }
        }
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

    private static string DescribeCompilationResult(object? result, out bool succeeded)
    {
        if (result is null)
        {
            succeeded = true;
            return "Nessun risultato dettagliato restituito dal compilatore.";
        }

        var state = GetPropertyValue(result, "State")?.ToString();
        var messages = GetPropertyValue(result, "Messages");
        var messageList = EnumerateObjects(messages).ToList();
        var messageCount = messageList.Count;
        var sampleMessages = new List<string>();
        var hasErrorMessage = false;

        foreach (var message in messageList.Take(5))
        {
            var description = DescribeCompilationMessage(message);
            if (!string.IsNullOrWhiteSpace(description))
            {
                sampleMessages.Add(description);
            }

            if (MessageLooksLikeError(message) || DescriptionIndicatesError(description))
            {
                hasErrorMessage = true;
            }
        }

        succeeded = !StateIndicatesError(state) && !hasErrorMessage;

        var details = sampleMessages.Count > 0
            ? $" SampleMessages=[{string.Join(" | ", sampleMessages)}]."
            : string.Empty;

        return $"State={state ?? "n/a"}, Messages={messageCount}.{details}";
    }

    private static string DescribeCompilationMessage(object message)
    {
        var description = GetPropertyValue(message, "Description")?.ToString();
        var text = GetPropertyValue(message, "Text")?.ToString();
        var category = GetPropertyValue(message, "Category")?.ToString();
        var severity = GetPropertyValue(message, "Severity")?.ToString();

        var parts = new[] { severity, category, description, text }
            .Where(part => !string.IsNullOrWhiteSpace(part))
            .Distinct()
            .ToArray();

        return parts.Length == 0 ? message.ToString() ?? string.Empty : string.Join(" - ", parts);
    }

    private static bool MessageLooksLikeError(object message)
    {
        var severity = GetPropertyValue(message, "Severity")?.ToString();
        var category = GetPropertyValue(message, "Category")?.ToString();

        return StateIndicatesError(severity) || StateIndicatesError(category);
    }

    private static bool StateIndicatesError(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var normalized = value.Trim().ToLowerInvariant();
        return normalized.Contains("error")
            || normalized.Contains("failed")
            || normalized.Contains("fault")
            || normalized.Contains("invalid");
    }

    private static bool DescriptionIndicatesError(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var normalized = value.Trim().ToLowerInvariant();
        if (normalized.Contains("errors: 0"))
        {
            return false;
        }

        return normalized.Contains("error")
            || normalized.Contains("failed")
            || normalized.Contains("fault")
            || normalized.Contains("invalid");
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

    private static bool ContainsIgnoreCase(string value, string fragment)
    {
        if (string.IsNullOrEmpty(value) || string.IsNullOrEmpty(fragment))
        {
            return false;
        }

        return value.IndexOf(fragment, StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private static bool IsRootBlockGroupName(object blockGroup, string candidate)
    {
        var normalized = (candidate ?? string.Empty).Trim();
        if (normalized.Length == 0)
        {
            return false;
        }

        var actualName = DescribeObject(blockGroup);
        if (!string.IsNullOrWhiteSpace(actualName)
            && string.Equals(actualName, normalized, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return string.Equals(normalized, "Program blocks", StringComparison.OrdinalIgnoreCase)
            || string.Equals(normalized, "Programma blocchi", StringComparison.OrdinalIgnoreCase);
    }
}
