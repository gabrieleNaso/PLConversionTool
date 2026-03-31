using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public interface IReflectionOpennessRuntime
{
    OpennessDiagnosticsResponse GetDiagnostics();

    Task<OpennessExecutionResult> ExecuteAsync(TiaJob job, CancellationToken cancellationToken);
}
