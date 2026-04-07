namespace PLConversionTool.TiaAgent.Contracts;

public sealed record JobRequest(
    string Operation,
    string ArtifactPath,
    string? ProjectPath,
    string? TargetPath,
    string? TargetName,
    bool SaveProject,
    string? Notes
);
