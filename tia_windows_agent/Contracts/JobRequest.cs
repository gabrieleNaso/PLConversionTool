namespace PLConversionTool.TiaAgent.Contracts;

public sealed record JobRequest(
    string Operation,
    string ArtifactPath,
    string? ProjectPath,
    string? Notes
);
