namespace PLConversionTool.TiaAgent.Contracts;

public sealed record StatusResponse(
    string Service,
    string Mode,
    string TiaPortalVersion,
    string ProjectRoot,
    string OutputDirectory,
    string TempDirectory,
    IReadOnlyList<string> SupportedOperations
);
