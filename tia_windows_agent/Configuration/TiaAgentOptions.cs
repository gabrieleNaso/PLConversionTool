namespace PLConversionTool.TiaAgent.Configuration;

public sealed class TiaAgentOptions
{
    public const string SectionName = "TiaAgent";

    public string ListenUrl { get; set; } = "http://0.0.0.0:8050";

    public string ProjectRoot { get; set; } = @"C:\PLConversionTool";

    public string OutputDirectory { get; set; } = @"C:\PLConversionTool\output";

    public string TempDirectory { get; set; } = @"C:\PLConversionTool\tmp";

    public string TiaPortalVersion { get; set; } = "V20";

    public string OpennessMode { get; set; } = "stub";

    public string SiemensAssemblyDirectory { get; set; } =
        @"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20";

    public string DefaultProjectPath { get; set; }

    public bool LaunchUi { get; set; }

    public IReadOnlyList<string> AllowedOrigins { get; set; } = new[] { "http://localhost:8010" };
}
