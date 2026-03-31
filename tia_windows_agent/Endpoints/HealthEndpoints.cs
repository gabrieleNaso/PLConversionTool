using Microsoft.Extensions.Options;
using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Services;

namespace PLConversionTool.TiaAgent.Endpoints;

public static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/health", (IOptions<TiaAgentOptions> options) =>
        {
            var config = options.Value;
            return Results.Ok(
                new
                {
                    status = "ok",
                    service = "tia-windows-agent",
                    mode = config.OpennessMode,
                    tiaPortalVersion = config.TiaPortalVersion,
                }
            );
        });

        app.MapGet("/api/status", (IOptions<TiaAgentOptions> options) =>
        {
            var config = options.Value;
            return Results.Ok(
                new StatusResponse(
                    Service: "tia-windows-agent",
                    Mode: config.OpennessMode,
                    TiaPortalVersion: config.TiaPortalVersion,
                    ProjectRoot: config.ProjectRoot,
                    OutputDirectory: config.OutputDirectory,
                    TempDirectory: config.TempDirectory,
                    SupportedOperations: ["import", "compile", "export"]
                )
            );
        });

        app.MapGet("/api/openness/diagnostics", (ITiaAgentService agentService) =>
        {
            return Results.Ok(agentService.GetDiagnostics());
        });

        return app;
    }
}
