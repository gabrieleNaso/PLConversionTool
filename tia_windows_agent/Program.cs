using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Endpoints;
using PLConversionTool.TiaAgent.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Configuration
    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
    .AddJsonFile("appsettings.Local.json", optional: true, reloadOnChange: true)
    .AddEnvironmentVariables();

var listenUrl =
    builder.Configuration[$"{TiaAgentOptions.SectionName}:ListenUrl"] ?? "http://0.0.0.0:8050";

builder.WebHost.UseUrls(listenUrl);

builder.Services.Configure<TiaAgentOptions>(
    builder.Configuration.GetSection(TiaAgentOptions.SectionName)
);
builder.Services.AddSingleton<IJobStore, InMemoryJobStore>();
builder.Services.AddSingleton<IReflectionOpennessRuntime, ReflectionOpennessRuntime>();
builder.Services.AddSingleton<ITiaAgentService, TiaAgentService>();

var app = builder.Build();

app.MapHealthEndpoints();
app.MapJobEndpoints();

app.Run();
