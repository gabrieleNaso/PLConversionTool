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
    private sealed record ExportBlockEntry(object Block, string RelativeGroupPath);
    private static readonly object CompileIntrospectionSync = new();
    private static CompileIntrospectionResponse? lastCompileIntrospection;

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

    public CompileIntrospectionResponse GetLastCompileIntrospection()
    {
        lock (CompileIntrospectionSync)
        {
            return lastCompileIntrospection ?? new CompileIntrospectionResponse(
                Status: "empty",
                CapturedAtUtc: null,
                JobId: null,
                Candidate: null,
                Summary: null,
                ResultProperties: Array.Empty<string>(),
                FirstMessageProperties: Array.Empty<string>(),
                Notes: "Nessuna introspezione compile registrata finora."
            );
        }
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

        if (job.Operation is "import" && !File.Exists(job.ArtifactPath) && !Directory.Exists(job.ArtifactPath))
        {
            throw new FileNotFoundException("ArtifactPath non trovato.", job.ArtifactPath);
        }

        if (job.Operation is "export")
        {
            var outputDirectory = Path.GetExtension(job.ArtifactPath).Length > 0
                ? Path.GetDirectoryName(job.ArtifactPath)
                : job.ArtifactPath;

            if (string.IsNullOrWhiteSpace(outputDirectory))
            {
                throw new InvalidOperationException("ArtifactPath non valido per export.");
            }
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
            CaptureCompileIntrospection(job, candidate, result, summary);
            await Task.CompletedTask;

            if (!compileSucceeded)
            {
                var alternativeDiagnostics = CollectAlternativeCompileDiagnostics(
                    result,
                    candidate,
                    project,
                    plcSoftware
                );
                var alternativeDetails = string.IsNullOrWhiteSpace(alternativeDiagnostics)
                    ? string.Empty
                    : $" AlternativeDiagnostics=[{alternativeDiagnostics}].";

                return new OpennessExecutionResult(
                    "blocked",
                    $"Compile eseguita ma TIA ha restituito un esito non valido su '{DescribeObject(candidate)}'. {summary}{alternativeDetails}"
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

        var targetGroup = ResolveBlockGroup(rootBlockGroup, job.TargetPath, createMissing: true);
        var importTarget = GetPropertyValue(targetGroup, "Blocks") ?? targetGroup;
        var importFiles = ResolveImportFiles(job.ArtifactPath);

        var importedCount = 0;
        var importedFiles = new List<string>();
        foreach (var importFile in importFiles)
        {
            if (!TryInvokeImport(importTarget, importFile, out var importDescription))
            {
                var available = DescribePublicMethods(importTarget, "Import");
                return new OpennessExecutionResult(
                    "blocked",
                    $"Import non riuscito per '{importFile.FullName}' su {importTarget.GetType().FullName}. {importDescription} Metodi osservati: {available}"
                );
            }

            importedCount++;
            importedFiles.Add(importFile.Name);
        }

        if (job.SaveProject)
        {
            TrySaveProject(project);
        }

        await Task.CompletedTask;
        return new OpennessExecutionResult(
            "completed",
            $"Import completato in '{DescribeObject(targetGroup)}'. File importati: {importedCount}. [{string.Join(", ", importedFiles.Take(10))}{(importedFiles.Count > 10 ? ", ..." : string.Empty)}]"
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

        var exportAsDirectory = Path.GetExtension(job.ArtifactPath).Length == 0;
        if (exportAsDirectory && string.IsNullOrWhiteSpace(job.TargetName))
        {
            return await ExportMultipleAsync(project, rootBlockGroup, job, cancellationToken);
        }

        var effectiveArtifactPath = exportAsDirectory
            ? Path.Combine(job.ArtifactPath, $"{SanitizePathSegment(blockName!)}.xml")
            : job.ArtifactPath;

        var block = FindBlockByName(rootBlockGroup, blockName!)
            ?? throw new InvalidOperationException(
                $"Blocco '{blockName}' non trovato nel progetto. Specifica TargetName se necessario."
            );

        var exportFile = new FileInfo(effectiveArtifactPath);
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
            $"Compile automatica preliminare riuscita. Export completato dal blocco '{blockName}' verso '{effectiveArtifactPath}'. {exportDescription}"
        );
    }

    private static async Task<OpennessExecutionResult> ExportMultipleAsync(
        object project,
        object rootBlockGroup,
        TiaJob job,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var targetGroup = ResolveBlockGroup(rootBlockGroup, job.TargetPath);
        var outputRoot = job.ArtifactPath;
        Directory.CreateDirectory(outputRoot);

        var blocks = EnumerateBlocksForExport(targetGroup, prefix: string.Empty).ToList();
        if (blocks.Count == 0)
        {
            return new OpennessExecutionResult(
                "blocked",
                $"Nessun blocco esportabile trovato nel gruppo '{DescribeObject(targetGroup)}'."
            );
        }

        var exportedFiles = new List<string>();
        foreach (var blockEntry in blocks)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var relativePath = BuildRelativeExportPath(blockEntry.RelativeGroupPath, DescribeObject(blockEntry.Block));
            var destinationPath = Path.Combine(outputRoot, relativePath);
            var destinationFile = new FileInfo(destinationPath);
            Directory.CreateDirectory(
                destinationFile.DirectoryName
                    ?? throw new InvalidOperationException("Directory export non valida.")
            );

            if (!TryInvokeExport(blockEntry.Block, destinationFile, out var exportDescription))
            {
                var available = DescribePublicMethods(blockEntry.Block, "Export");
                return new OpennessExecutionResult(
                    "blocked",
                    $"Export non riuscito per il blocco '{DescribeObject(blockEntry.Block)}' verso '{destinationFile.FullName}'. {exportDescription} Metodi osservati: {available}"
                );
            }

            exportedFiles.Add(relativePath);
        }

        if (job.SaveProject)
        {
            TrySaveProject(project);
        }

        await Task.CompletedTask;
        return new OpennessExecutionResult(
            "completed",
            $"Compile automatica preliminare riuscita. Export cartella completato da '{DescribeObject(targetGroup)}'. File esportati: {exportedFiles.Count}. [{string.Join(", ", exportedFiles.Take(10))}{(exportedFiles.Count > 10 ? ", ..." : string.Empty)}]"
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

    private static object ResolveBlockGroup(
        object rootBlockGroup,
        string? targetPath,
        bool createMissing = false
    )
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

            var next = FindChildGroupByName(current, part);
            if (next is null && createMissing)
            {
                next = CreateChildGroup(current, part);
            }

            current = next
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

    private static object? CreateChildGroup(object blockGroup, string name)
    {
        foreach (var collectionName in new[] { "Groups", "GroupComposition", "BlockGroups" })
        {
            var collection = GetPropertyValue(blockGroup, collectionName);
            if (collection is null)
            {
                continue;
            }

            if (TryInvokeCreateGroup(collection, name))
            {
                return FindChildGroupByName(blockGroup, name);
            }
        }

        return null;
    }

    private static bool TryInvokeCreateGroup(object collection, string name)
    {
        foreach (var method in collection.GetType().GetMethods(BindingFlags.Instance | BindingFlags.Public))
        {
            if (
                !string.Equals(method.Name, "Create", StringComparison.Ordinal)
                && !string.Equals(method.Name, "CreateFrom", StringComparison.Ordinal)
                && !string.Equals(method.Name, "Add", StringComparison.Ordinal)
            )
            {
                continue;
            }

            var parameters = method.GetParameters();
            if (parameters.Length == 0 || parameters[0].ParameterType != typeof(string))
            {
                continue;
            }

            var args = new object?[parameters.Length];
            args[0] = name;

            var supported = true;
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
                    args[index] = false;
                    continue;
                }

                supported = false;
                break;
            }

            if (!supported)
            {
                continue;
            }

            try
            {
                method.Invoke(collection, args);
                return true;
            }
            catch
            {
                // Continua a provare altre overload compatibili.
            }
        }

        return false;
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

    private static IReadOnlyList<FileInfo> ResolveImportFiles(string artifactPath)
    {
        if (Directory.Exists(artifactPath))
        {
            var files = Directory.GetFiles(artifactPath, "*.xml", SearchOption.AllDirectories)
                .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
                .Select(path => new FileInfo(path))
                .ToList();

            if (files.Count == 0)
            {
                throw new InvalidOperationException(
                    $"Nessun file XML trovato nella directory di import '{artifactPath}'."
                );
            }

            return files;
        }

        return new[] { new FileInfo(artifactPath) };
    }

    private static IEnumerable<ExportBlockEntry> EnumerateBlocksForExport(
        object blockGroup,
        string prefix
    )
    {
        foreach (var block in EnumerateObjects(GetPropertyValue(blockGroup, "Blocks")))
        {
            yield return new ExportBlockEntry(block, prefix);
        }

        foreach (var childGroup in EnumerateObjects(GetPropertyValue(blockGroup, "Groups")))
        {
            var childName = SanitizePathSegment(DescribeObject(childGroup));
            var childPrefix = string.IsNullOrWhiteSpace(prefix)
                ? childName
                : Path.Combine(prefix, childName);

            foreach (var item in EnumerateBlocksForExport(childGroup, childPrefix))
            {
                yield return item;
            }
        }
    }

    private static string BuildRelativeExportPath(string relativeGroupPath, string blockName)
    {
        var safeFileName = $"{SanitizePathSegment(blockName)}.xml";
        return string.IsNullOrWhiteSpace(relativeGroupPath)
            ? safeFileName
            : Path.Combine(relativeGroupPath, safeFileName);
    }

    private static string SanitizePathSegment(string value)
    {
        var invalidChars = Path.GetInvalidFileNameChars();
        var sanitized = new string(
            value.Select(ch => invalidChars.Contains(ch) ? '_' : ch).ToArray()
        ).Trim();

        return string.IsNullOrWhiteSpace(sanitized) ? "unnamed" : sanitized;
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
        var topLevelMessages = EnumerateObjects(messages).ToList();
        var messageList = FlattenCompilationMessages(topLevelMessages).ToList();
        var messageCount = messageList.Count;
        var sampleMessages = new List<string>();
        var detailedMessages = new List<string>();
        var hasErrorMessage = false;
        var errorCount = 0;
        var warningCount = 0;

        foreach (var message in messageList.Take(50))
        {
            var description = DescribeCompilationMessage(message);
            var detailed = DescribeCompilationMessageDetailed(message);

            if (!string.IsNullOrWhiteSpace(description))
            {
                if (sampleMessages.Count < 5)
                {
                    sampleMessages.Add(description);
                }
            }

            if (!string.IsNullOrWhiteSpace(detailed))
            {
                detailedMessages.Add(detailed);
            }

            var isError = MessageLooksLikeError(message) || DescriptionIndicatesError(description);
            var isWarning = MessageLooksLikeWarning(message) || DescriptionIndicatesWarning(description);
            if (isError)
            {
                hasErrorMessage = true;
                errorCount++;
            }
            else if (isWarning)
            {
                warningCount++;
            }
        }

        succeeded = !StateIndicatesError(state) && !hasErrorMessage;

        var details = sampleMessages.Count > 0
            ? $" SampleMessages=[{string.Join(" | ", sampleMessages)}]."
            : string.Empty;

        var counters = $" ClassifiedErrors={errorCount}, ClassifiedWarnings={warningCount}.";
        var fullDetails = detailedMessages.Count > 0
            ? $" DetailedMessages=[{string.Join(" || ", detailedMessages)}]."
            : string.Empty;

        return $"State={state ?? "n/a"}, Messages={messageCount}.{counters}{details}{fullDetails}";
    }

    private static void CaptureCompileIntrospection(
        TiaJob job,
        object candidate,
        object? compileResult,
        string summary
    )
    {
        var firstMessage = compileResult is null
            ? null
            : EnumerateObjects(GetPropertyValue(compileResult, "Messages")).FirstOrDefault();
        var resultProperties = DescribeObjectProperties(compileResult, 40);
        var firstMessageProperties = DescribeObjectProperties(firstMessage, 40);

        var snapshot = new CompileIntrospectionResponse(
            Status: "captured",
            CapturedAtUtc: DateTimeOffset.UtcNow.ToString("O"),
            JobId: job.JobId,
            Candidate: DescribeObject(candidate),
            Summary: summary,
            ResultProperties: resultProperties,
            FirstMessageProperties: firstMessageProperties,
            Notes: firstMessage is null
                ? "Nessun messaggio disponibile nella collezione Messages."
                : "Snapshot del primo messaggio di compile."
        );

        lock (CompileIntrospectionSync)
        {
            lastCompileIntrospection = snapshot;
        }
    }

    private static IReadOnlyList<string> DescribeObjectProperties(object? target, int maxProperties)
    {
        if (target is null)
        {
            return Array.Empty<string>();
        }

        var entries = new List<string>();
        var properties = target.GetType()
            .GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(property => property.CanRead && property.GetIndexParameters().Length == 0)
            .OrderBy(property => property.Name)
            .Take(maxProperties);

        foreach (var property in properties)
        {
            object? value;
            try
            {
                value = property.GetValue(target);
            }
            catch (Exception ex)
            {
                entries.Add($"{property.Name}:{property.PropertyType.Name}=<error:{ex.GetType().Name}>");
                continue;
            }

            var serialized = SerializeDebugValue(value, 200);
            entries.Add($"{property.Name}:{property.PropertyType.Name}={serialized}");
        }

        return entries;
    }

    private static IEnumerable<object> FlattenCompilationMessages(IEnumerable<object> messages)
    {
        var queue = new Queue<object>(messages);
        var visited = new List<object>();

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            if (visited.Any(item => ReferenceEquals(item, current)))
            {
                continue;
            }

            visited.Add(current);
            yield return current;

            foreach (var nested in TryGetNestedCompilationMessages(current))
            {
                if (!visited.Any(item => ReferenceEquals(item, nested)))
                {
                    queue.Enqueue(nested);
                }
            }
        }
    }

    private static IEnumerable<object> TryGetNestedCompilationMessages(object message)
    {
        var properties = message.GetType()
            .GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(property =>
                property.CanRead
                && property.GetIndexParameters().Length == 0
                && IsPotentialMessageContainerProperty(property)
            );

        foreach (var property in properties)
        {
            object? value;
            try
            {
                value = property.GetValue(message);
            }
            catch
            {
                continue;
            }

            foreach (var nested in EnumerateObjects(value))
            {
                if (nested is string)
                {
                    continue;
                }

                yield return nested;
            }
        }
    }

    private static bool IsPotentialMessageContainerProperty(PropertyInfo property)
    {
        if (property.PropertyType == typeof(string))
        {
            return false;
        }

        if (typeof(IEnumerable).IsAssignableFrom(property.PropertyType))
        {
            return true;
        }

        var normalized = property.Name.Trim().ToLowerInvariant();
        return normalized.Contains("message")
            || normalized.Contains("inner")
            || normalized.Contains("child")
            || normalized.Contains("detail")
            || normalized.Contains("result")
            || normalized.Contains("diagnostic");
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

    private static string DescribeCompilationMessageDetailed(object message)
    {
        var baseMessage = DescribeCompilationMessage(message);
        var associatedObject = GetPropertyValue(message, "AssociatedObject");
        var sourceObject = GetPropertyValue(message, "SourceObject");
        var objectName = associatedObject is not null
            ? DescribeObject(associatedObject)
            : sourceObject is not null
                ? DescribeObject(sourceObject)
                : null;
        var identifier = GetPropertyValue(message, "Identifier")?.ToString();
        var number = GetPropertyValue(message, "Number")?.ToString();
        var objectPath = GetPropertyValue(message, "Path")?.ToString();

        var contextParts = new[] { objectName, identifier, number, objectPath }
            .Where(part => !string.IsNullOrWhiteSpace(part))
            .Distinct()
            .ToArray();

        if (contextParts.Length == 0)
        {
            var debugSnapshot = BuildMessageDebugSnapshot(message);
            return string.IsNullOrWhiteSpace(debugSnapshot)
                ? baseMessage
                : $"{baseMessage} [Debug: {debugSnapshot}]";
        }

        var context = string.Join(" | ", contextParts);
        var debug = BuildMessageDebugSnapshot(message);
        return string.IsNullOrWhiteSpace(debug)
            ? $"{baseMessage} [Context: {context}]"
            : $"{baseMessage} [Context: {context}] [Debug: {debug}]";
    }

    private static string CollectAlternativeCompileDiagnostics(
        object? compileResult,
        object compileTarget,
        object project,
        object? plcSoftware
    )
    {
        var probes = new List<(string Name, object? Target)>
        {
            ("CompileResult", compileResult),
            ("CompileTarget", compileTarget),
            ("Project", project),
            ("PlcSoftware", plcSoftware)
        };

        var interestingPropertyNames = new[]
        {
            "Messages", "Diagnostics", "DiagnosticMessages", "CompilerMessages",
            "Errors", "Warnings", "Entries", "Results", "InnerResults", "Items"
        };

        var snippets = new List<string>();
        foreach (var (name, target) in probes)
        {
            if (target is null)
            {
                continue;
            }

            foreach (var propertyName in interestingPropertyNames)
            {
                var value = GetPropertyValue(target, propertyName);
                if (value is null)
                {
                    continue;
                }

                var serialized = SerializeDebugValue(value, 240);
                if (!string.IsNullOrWhiteSpace(serialized))
                {
                    snippets.Add($"{name}.{propertyName}={serialized}");
                }
            }

            var methods = DescribePublicMethods(target, "GetDiagnostics");
            if (!string.Equals(methods, "nessuno", StringComparison.OrdinalIgnoreCase))
            {
                snippets.Add($"{name}.GetDiagnosticsMethods={methods}");
            }
        }

        return snippets.Count == 0 ? string.Empty : string.Join(" | ", snippets.Distinct());
    }

    private static string BuildMessageDebugSnapshot(object message)
    {
        const int maxProperties = 25;
        const int maxValueLength = 240;
        var fields = new List<string>();

        var properties = message.GetType()
            .GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(property => property.CanRead && property.GetIndexParameters().Length == 0)
            .OrderBy(property => property.Name)
            .Take(maxProperties);

        foreach (var property in properties)
        {
            object? value;
            try
            {
                value = property.GetValue(message);
            }
            catch
            {
                continue;
            }

            var serialized = SerializeDebugValue(value, maxValueLength);
            if (!string.IsNullOrWhiteSpace(serialized))
            {
                fields.Add($"{property.Name}={serialized}");
            }
        }

        return fields.Count == 0 ? string.Empty : string.Join("; ", fields);
    }

    private static string SerializeDebugValue(object? value, int maxValueLength)
    {
        if (value is null)
        {
            return "null";
        }

        if (value is string text)
        {
            return Truncate(text, maxValueLength);
        }

        if (value is IEnumerable enumerable && value is not string)
        {
            var samples = new List<string>();
            foreach (var item in enumerable)
            {
                if (item is null)
                {
                    continue;
                }

                var label = item is string itemText ? itemText : item.ToString() ?? item.GetType().Name;
                samples.Add(Truncate(label, 80));
                if (samples.Count >= 3)
                {
                    break;
                }
            }

            return samples.Count == 0 ? "[]" : $"[{string.Join(", ", samples)}]";
        }

        return Truncate(value.ToString() ?? value.GetType().Name, maxValueLength);
    }

    private static string Truncate(string value, int maxLength)
    {
        if (string.IsNullOrEmpty(value) || value.Length <= maxLength)
        {
            return value;
        }

        return value.Substring(0, maxLength) + "...";
    }

    private static bool MessageLooksLikeError(object message)
    {
        var severity = GetPropertyValue(message, "Severity")?.ToString();
        var category = GetPropertyValue(message, "Category")?.ToString();

        return StateIndicatesError(severity) || StateIndicatesError(category);
    }

    private static bool MessageLooksLikeWarning(object message)
    {
        var severity = GetPropertyValue(message, "Severity")?.ToString();
        var category = GetPropertyValue(message, "Category")?.ToString();

        return StateIndicatesWarning(severity) || StateIndicatesWarning(category);
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

    private static bool StateIndicatesWarning(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var normalized = value.Trim().ToLowerInvariant();
        return normalized.Contains("warn");
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

    private static bool DescriptionIndicatesWarning(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var normalized = value.Trim().ToLowerInvariant();
        return normalized.Contains("warning")
            || normalized.Contains("warn");
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
