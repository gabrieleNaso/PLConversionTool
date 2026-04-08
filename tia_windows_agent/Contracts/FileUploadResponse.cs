namespace PLConversionTool.TiaAgent.Contracts;

public sealed record FileUploadResponse(
    string StoredPath,
    long SizeBytes
);
