namespace PLConversionTool.TiaAgent.Contracts;

public sealed record JobResponse(
    string JobId,
    string Status,
    string Operation,
    string ArtifactPath,
    string? ProjectPath,
    string? TargetPath,
    string? TargetName,
    bool SaveProject,
    string? Notes,
    string? Detail
);
