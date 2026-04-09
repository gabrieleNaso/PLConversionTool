namespace PLConversionTool.TiaAgent.Contracts;

public sealed record FileReadResponse(
    string SourcePath,
    string ContentBase64,
    long SizeBytes
);
