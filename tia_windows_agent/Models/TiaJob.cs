namespace PLConversionTool.TiaAgent.Models;

public sealed record TiaJob(
    string JobId,
    string Operation,
    string ArtifactPath,
    string? ProjectPath,
    string? TargetPath,
    string? TargetName,
    bool SaveProject,
    string? Notes,
    string Status,
    string? Detail,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc
);
