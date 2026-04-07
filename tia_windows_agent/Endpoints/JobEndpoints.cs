using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Services;

namespace PLConversionTool.TiaAgent.Endpoints;

public static class JobEndpoints
{
    public static IEndpointRouteBuilder MapJobEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/api/jobs/import", CreateHandler("import"));
        app.MapPost("/api/jobs/compile", CreateHandler("compile"));
        app.MapPost("/api/jobs/export", CreateHandler("export"));

        app.MapGet("/api/jobs/{jobId}", (string jobId, IJobStore jobStore) =>
        {
            var job = jobStore.Get(jobId);
            return job is null ? Results.NotFound() : Results.Ok(job);
        });

        app.MapGet("/api/jobs", (IJobStore jobStore) => Results.Ok(jobStore.List()));

        return app;
    }

    private static Delegate CreateHandler(string operation)
    {
        return async (JobRequest request, ITiaAgentService agentService, IJobStore jobStore, CancellationToken cancellationToken) =>
        {
            var normalizedRequest = request with { Operation = operation };
            var jobId = await agentService.QueueJobAsync(normalizedRequest, cancellationToken);
            var job = jobStore.Get(jobId)!;

            return Results.Accepted(
                $"/api/jobs/{jobId}",
                new JobResponse(
                    JobId: job.JobId,
                    Status: job.Status,
                    Operation: job.Operation,
                    ArtifactPath: job.ArtifactPath,
                    ProjectPath: job.ProjectPath,
                    TargetPath: job.TargetPath,
                    TargetName: job.TargetName,
                    SaveProject: job.SaveProject,
                    Notes: job.Notes,
                    Detail: job.Detail
                )
            );
        };
    }
}
