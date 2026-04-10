using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public sealed class TiaAgentService(
    IJobStore jobStore,
    TiaAgentOptions options,
    IReflectionOpennessRuntime runtime
) : ITiaAgentService
{
    private readonly SemaphoreSlim jobLock = new(1, 1);

    public Task<string> QueueJobAsync(JobRequest request, CancellationToken cancellationToken)
    {
        var now = DateTimeOffset.UtcNow;
        var jobId = $"job-{Guid.NewGuid():N}";
        var effectiveProjectPath = string.IsNullOrWhiteSpace(request.ProjectPath)
            ? options.DefaultProjectPath
            : request.ProjectPath;

        jobStore.Add(
            new TiaJob(
                JobId: jobId,
                Operation: request.Operation,
                ArtifactPath: request.ArtifactPath,
                ProjectPath: effectiveProjectPath,
                TargetPath: request.TargetPath,
                TargetName: request.TargetName,
                SaveProject: request.SaveProject,
                Notes: request.Notes,
                Status: "queued",
                Detail: "Job accodato.",
                CreatedAtUtc: now,
                UpdatedAtUtc: now
            )
        );

        _ = Task.Run(() => ProcessJobAsync(jobId, cancellationToken), CancellationToken.None);
        return Task.FromResult(jobId);
    }

    public OpennessDiagnosticsResponse GetDiagnostics()
    {
        return runtime.GetDiagnostics();
    }

    public CompileIntrospectionResponse GetLastCompileIntrospection()
    {
        return runtime.GetLastCompileIntrospection();
    }

    private async Task ProcessJobAsync(string jobId, CancellationToken cancellationToken)
    {
        await jobLock.WaitAsync(CancellationToken.None);

        try
        {
            MarkRunning(jobId);
            var job = jobStore.Get(jobId)!;
            var result = await runtime.ExecuteAsync(job, cancellationToken);

            jobStore.Update(
                jobId,
                current => current with
                {
                    Status = result.Status,
                    Detail = result.Detail,
                    UpdatedAtUtc = DateTimeOffset.UtcNow,
                }
            );
        }
        catch (Exception ex)
        {
            jobStore.Update(
                jobId,
                current => current with
                {
                    Status = "failed",
                    Detail = BuildExceptionDetail(ex),
                    UpdatedAtUtc = DateTimeOffset.UtcNow,
                }
            );
        }
        finally
        {
            jobLock.Release();
        }
    }

    private void MarkRunning(string jobId)
    {
        jobStore.Update(
            jobId,
            current => current with
            {
                Status = "running",
                Detail = "Job in esecuzione verso il runtime TIA.",
                UpdatedAtUtc = DateTimeOffset.UtcNow,
            }
        );
    }

    private static string BuildExceptionDetail(Exception exception)
    {
        var chain = new List<string>();
        var current = exception;

        while (current is not null)
        {
            chain.Add($"{current.GetType().FullName}: {current.Message}");
            current = current.InnerException!;
        }

        return string.Join(" | INNER -> ", chain);
    }
}
