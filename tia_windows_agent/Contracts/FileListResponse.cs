namespace PLConversionTool.TiaAgent.Contracts;

public sealed record FileListResponse(
    string RootPath,
    IReadOnlyList<string> Files
);
