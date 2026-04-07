using System.IO;
using System.Net;
using System.Text;
using System.Web.Script.Serialization;
using PLConversionTool.TiaAgent.Configuration;
using PLConversionTool.TiaAgent.Contracts;
using PLConversionTool.TiaAgent.Services;

namespace PLConversionTool.TiaAgent;

public static class Program
{
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();

    public static void Main()
    {
        var options = LoadOptions();
        var jobStore = new InMemoryJobStore();
        var runtime = new ReflectionOpennessRuntime(options);
        var agentService = new TiaAgentService(jobStore, options, runtime);

        using (var listener = new HttpListener())
        {
            var prefix = NormalizePrefix(options.ListenUrl);
            listener.Prefixes.Add(prefix);
            listener.Start();

            Console.WriteLine($"TIA Windows Agent in ascolto su {prefix}");

            while (true)
            {
                var context = listener.GetContext();
                try
                {
                    HandleRequest(context, options, jobStore, agentService);
                }
                catch (Exception ex)
                {
                    WriteJson(context, 500, new
                    {
                        error = "internal_server_error",
                        detail = ex.ToString(),
                    });
                }
            }
        }
    }

    private static void HandleRequest(
        HttpListenerContext context,
        TiaAgentOptions options,
        IJobStore jobStore,
        ITiaAgentService agentService
    )
    {
        AddCorsHeaders(context, options);

        if (context.Request.HttpMethod == "OPTIONS")
        {
            context.Response.StatusCode = 204;
            context.Response.Close();
            return;
        }

        var path = context.Request.Url?.AbsolutePath ?? "/";
        var method = context.Request.HttpMethod.ToUpperInvariant();

        if (method == "GET" && path == "/health")
        {
            WriteJson(context, 200, new
            {
                status = "ok",
                service = "tia-windows-agent",
                mode = options.OpennessMode,
                tiaPortalVersion = options.TiaPortalVersion,
            });
            return;
        }

        if (method == "GET" && path == "/api/status")
        {
            WriteJson(context, 200, new StatusResponse(
                Service: "tia-windows-agent",
                Mode: options.OpennessMode,
                TiaPortalVersion: options.TiaPortalVersion,
                ProjectRoot: options.ProjectRoot,
                OutputDirectory: options.OutputDirectory,
                TempDirectory: options.TempDirectory,
                SupportedOperations: new[] { "import", "compile", "export" }
            ));
            return;
        }

        if (method == "GET" && path == "/api/openness/diagnostics")
        {
            WriteJson(context, 200, agentService.GetDiagnostics());
            return;
        }

        if (method == "GET" && path == "/api/jobs")
        {
            WriteJson(context, 200, jobStore.List());
            return;
        }

        if (method == "GET" && path.StartsWith("/api/jobs/", StringComparison.OrdinalIgnoreCase))
        {
            var jobId = path.Substring("/api/jobs/".Length);
            var job = jobStore.Get(jobId);
            if (job is null)
            {
                WriteJson(context, 404, new { error = "not_found" });
                return;
            }

            WriteJson(context, 200, job);
            return;
        }

        if (method == "POST" && path == "/api/jobs/import")
        {
            CreateJob(context, "import", agentService, jobStore);
            return;
        }

        if (method == "POST" && path == "/api/jobs/compile")
        {
            CreateJob(context, "compile", agentService, jobStore);
            return;
        }

        if (method == "POST" && path == "/api/jobs/export")
        {
            CreateJob(context, "export", agentService, jobStore);
            return;
        }

        WriteJson(context, 404, new { error = "not_found", path });
    }

    private static void CreateJob(
        HttpListenerContext context,
        string operation,
        ITiaAgentService agentService,
        IJobStore jobStore
    )
    {
        var requestBody = ReadBody(context.Request);
        var request = ParseJobRequest(requestBody, operation);
        var jobId = agentService.QueueJobAsync(request, CancellationToken.None).GetAwaiter().GetResult();
        var job = jobStore.Get(jobId);

        WriteJson(context, 202, new JobResponse(
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
        ));
    }

    private static JobRequest ParseJobRequest(string json, string operation)
    {
        var payload = string.IsNullOrWhiteSpace(json)
            ? new Dictionary<string, object>()
            : Json.Deserialize<Dictionary<string, object>>(json);

        return new JobRequest(
            Operation: operation,
            ArtifactPath: GetString(payload, "artifactPath"),
            ProjectPath: GetOptionalString(payload, "projectPath"),
            TargetPath: GetOptionalString(payload, "targetPath"),
            TargetName: GetOptionalString(payload, "targetName"),
            SaveProject: GetBool(payload, "saveProject"),
            Notes: GetOptionalString(payload, "notes")
        );
    }

    private static TiaAgentOptions LoadOptions()
    {
        var basePath = AppDomain.CurrentDomain.BaseDirectory;
        var appsettingsPath = Path.Combine(basePath, "appsettings.json");
        var localPath = Path.Combine(basePath, "appsettings.Local.json");

        var options = ReadOptionsFile(appsettingsPath);
        if (File.Exists(localPath))
        {
            MergeOptions(options, ReadOptionsFile(localPath));
        }

        return options;
    }

    private static TiaAgentOptions ReadOptionsFile(string path)
    {
        var json = File.ReadAllText(path, Encoding.UTF8);
        var root = Json.Deserialize<Dictionary<string, object>>(json);
        var rawSection = root.ContainsKey(TiaAgentOptions.SectionName)
            ? root[TiaAgentOptions.SectionName] as Dictionary<string, object>
            : null;

        if (rawSection == null)
        {
            throw new InvalidOperationException($"Sezione '{TiaAgentOptions.SectionName}' non trovata in {path}.");
        }

        return new TiaAgentOptions
        {
            ListenUrl = GetOptionalString(rawSection, "ListenUrl") ?? "http://0.0.0.0:8050",
            ProjectRoot = GetOptionalString(rawSection, "ProjectRoot") ?? @"C:\PLConversionTool",
            OutputDirectory = GetOptionalString(rawSection, "OutputDirectory") ?? @"C:\PLConversionTool\output",
            TempDirectory = GetOptionalString(rawSection, "TempDirectory") ?? @"C:\PLConversionTool\tmp",
            TiaPortalVersion = GetOptionalString(rawSection, "TiaPortalVersion") ?? "V20",
            OpennessMode = GetOptionalString(rawSection, "OpennessMode") ?? "stub",
            SiemensAssemblyDirectory = GetOptionalString(rawSection, "SiemensAssemblyDirectory")
                ?? @"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20",
            DefaultProjectPath = GetOptionalString(rawSection, "DefaultProjectPath"),
            LaunchUi = GetBool(rawSection, "LaunchUi"),
            AllowedOrigins = GetStringArray(rawSection, "AllowedOrigins"),
        };
    }

    private static void MergeOptions(TiaAgentOptions target, TiaAgentOptions source)
    {
        target.ListenUrl = source.ListenUrl ?? target.ListenUrl;
        target.ProjectRoot = source.ProjectRoot ?? target.ProjectRoot;
        target.OutputDirectory = source.OutputDirectory ?? target.OutputDirectory;
        target.TempDirectory = source.TempDirectory ?? target.TempDirectory;
        target.TiaPortalVersion = source.TiaPortalVersion ?? target.TiaPortalVersion;
        target.OpennessMode = source.OpennessMode ?? target.OpennessMode;
        target.SiemensAssemblyDirectory = source.SiemensAssemblyDirectory ?? target.SiemensAssemblyDirectory;
        target.DefaultProjectPath = source.DefaultProjectPath ?? target.DefaultProjectPath;
        target.LaunchUi = source.LaunchUi;
        if (source.AllowedOrigins != null && source.AllowedOrigins.Count > 0)
        {
            target.AllowedOrigins = source.AllowedOrigins;
        }
    }

    private static string NormalizePrefix(string listenUrl)
    {
        var prefix = listenUrl.Trim();
        if (!prefix.EndsWith("/", StringComparison.Ordinal))
        {
            prefix += "/";
        }

        if (prefix.Contains("0.0.0.0"))
        {
            prefix = prefix.Replace("0.0.0.0", "+");
        }

        return prefix;
    }

    private static string ReadBody(HttpListenerRequest request)
    {
        using (var reader = new StreamReader(request.InputStream, request.ContentEncoding ?? Encoding.UTF8))
        {
            return reader.ReadToEnd();
        }
    }

    private static void WriteJson(HttpListenerContext context, int statusCode, object payload)
    {
        var json = Json.Serialize(payload);
        var bytes = Encoding.UTF8.GetBytes(json);

        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json; charset=utf-8";
        context.Response.ContentEncoding = Encoding.UTF8;
        context.Response.ContentLength64 = bytes.LongLength;
        context.Response.OutputStream.Write(bytes, 0, bytes.Length);
        context.Response.OutputStream.Flush();
        context.Response.Close();
    }

    private static void AddCorsHeaders(HttpListenerContext context, TiaAgentOptions options)
    {
        var origin = context.Request.Headers["Origin"];
        if (!string.IsNullOrWhiteSpace(origin) &&
            options.AllowedOrigins.Any(item => string.Equals(item, origin, StringComparison.OrdinalIgnoreCase)))
        {
            context.Response.Headers["Access-Control-Allow-Origin"] = origin;
        }

        context.Response.Headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS";
        context.Response.Headers["Access-Control-Allow-Headers"] = "Content-Type";
    }

    private static string GetString(IDictionary<string, object> payload, string key)
    {
        var value = GetOptionalString(payload, key);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"Campo obbligatorio mancante: {key}");
        }

        return value;
    }

    private static string GetOptionalString(IDictionary<string, object> payload, string key)
    {
        if (!payload.ContainsKey(key) || payload[key] == null)
        {
            return null;
        }

        return payload[key].ToString();
    }

    private static bool GetBool(IDictionary<string, object> payload, string key)
    {
        if (!payload.ContainsKey(key) || payload[key] == null)
        {
            return false;
        }

        var value = payload[key];
        if (value is bool boolValue)
        {
            return boolValue;
        }

        bool parsed;
        return bool.TryParse(value.ToString(), out parsed) && parsed;
    }

    private static IReadOnlyList<string> GetStringArray(IDictionary<string, object> payload, string key)
    {
        if (!payload.ContainsKey(key) || payload[key] == null)
        {
            return new[] { "http://localhost:8010" };
        }

        var raw = payload[key] as object[];
        if (raw == null)
        {
            var arrayList = payload[key] as ArrayList;
            if (arrayList != null)
            {
                return arrayList.Cast<object>().Select(item => item.ToString()).ToList();
            }

            return new[] { payload[key].ToString() };
        }

        return raw.Select(item => item.ToString()).ToList();
    }
}
