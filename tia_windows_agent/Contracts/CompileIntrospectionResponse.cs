namespace PLConversionTool.TiaAgent.Contracts;

public sealed record CompileIntrospectionResponse(
    string Status,
    string? CapturedAtUtc,
    string? JobId,
    string? Candidate,
    string? Summary,
    IReadOnlyList<string> ResultProperties,
    IReadOnlyList<string> FirstMessageProperties,
    string? Notes
);
