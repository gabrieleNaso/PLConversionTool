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
                "Modalita' real attiva: il runtime tentera' il caricamento reflection delle DLL Siemens."
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

        var probeResult = await ProbeRuntimeAsync(diagnostics.SiemensEngineeringAssemblyPath, config, cancellationToken);

        return new OpennessExecutionResult(
            "prepared",
            $"Probe Openness riuscita. Job {job.Operation} pronto per integrazione concreta. {probeResult}"
        );
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

    private static Task<string> ProbeRuntimeAsync(
        string engineeringAssemblyPath,
        TiaAgentOptions config,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        var assembly = Assembly.LoadFrom(engineeringAssemblyPath);
        var tiaPortalType = assembly.GetType("Siemens.Engineering.TiaPortal");
        var tiaPortalModeType = assembly.GetType("Siemens.Engineering.TiaPortalMode");

        if (tiaPortalType is null || tiaPortalModeType is null)
        {
            throw new InvalidOperationException(
                "Tipi Siemens.Engineering.TiaPortal o Siemens.Engineering.TiaPortalMode non trovati."
            );
        }

        var desiredModeName = config.LaunchUi ? "WithUserInterface" : "WithoutUserInterface";
        var mode = Enum.Parse(tiaPortalModeType, desiredModeName, ignoreCase: false);

        using var tiaPortal = Activator.CreateInstance(tiaPortalType, mode) as IDisposable;

        if (tiaPortal is null)
        {
            throw new InvalidOperationException("Impossibile creare una istanza TiaPortal via reflection.");
        }

        return Task.FromResult($"Istanza TiaPortal creata in modalita' {desiredModeName}.");
    }
}
