namespace PLConversionTool.TiaAgent.Contracts;

public sealed record OpennessDiagnosticsResponse(
    string Service,
    string Mode,
    string TiaPortalVersion,
    string SiemensAssemblyDirectory,
    bool SiemensAssemblyDirectoryExists,
    string SiemensEngineeringAssemblyPath,
    bool SiemensEngineeringAssemblyExists,
    string? DefaultProjectPath,
    bool DefaultProjectPathExists,
    bool LaunchUi,
    IReadOnlyList<string> Notes
);
