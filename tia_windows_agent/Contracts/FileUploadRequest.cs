namespace PLConversionTool.TiaAgent.Contracts;

public sealed record FileUploadRequest(
    string DestinationPath,
    string ContentBase64
);
