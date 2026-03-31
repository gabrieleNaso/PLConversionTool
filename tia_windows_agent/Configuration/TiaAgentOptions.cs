namespace PLConversionTool.TiaAgent.Configuration;

public sealed class TiaAgentOptions
{
    public const string SectionName = "TiaAgent";

    public string ListenUrl { get; init; } = "http://0.0.0.0:8050";

    public string ProjectRoot { get; init; } = @"C:\PLConversionTool";

    public string OutputDirectory { get; init; } = @"C:\PLConversionTool\output";

    public string TempDirectory { get; init; } = @"C:\PLConversionTool\tmp";

    public string TiaPortalVersion { get; init; } = "V20";

    public string OpennessMode { get; init; } = "stub";

    public string SiemensAssemblyDirectory { get; init; } =
        @"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20";

    public string? DefaultProjectPath { get; init; }

    public bool LaunchUi { get; init; }

    public IReadOnlyList<string> AllowedOrigins { get; init; } = ["http://localhost:8010"];
}
