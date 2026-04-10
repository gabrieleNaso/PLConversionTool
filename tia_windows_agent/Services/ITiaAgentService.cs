using PLConversionTool.TiaAgent.Contracts;

namespace PLConversionTool.TiaAgent.Services;

public interface ITiaAgentService
{
    Task<string> QueueJobAsync(JobRequest request, CancellationToken cancellationToken);

    OpennessDiagnosticsResponse GetDiagnostics();
    CompileIntrospectionResponse GetLastCompileIntrospection();
}
