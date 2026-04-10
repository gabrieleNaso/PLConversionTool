using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public interface IReflectionOpennessRuntime
{
    OpennessDiagnosticsResponse GetDiagnostics();
    CompileIntrospectionResponse GetLastCompileIntrospection();

    Task<OpennessExecutionResult> ExecuteAsync(TiaJob job, CancellationToken cancellationToken);
}
