using System.Collections.Concurrent;
using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public sealed class InMemoryJobStore : IJobStore
{
    private readonly ConcurrentDictionary<string, TiaJob> jobs = new();

    public void Add(TiaJob job)
    {
        jobs[job.JobId] = job;
    }

    public TiaJob Update(string jobId, Func<TiaJob, TiaJob> update)
    {
        return jobs.AddOrUpdate(
            jobId,
            _ => throw new KeyNotFoundException($"Job {jobId} non trovato."),
            (_, existing) => update(existing)
        );
    }

    public TiaJob? Get(string jobId)
    {
        jobs.TryGetValue(jobId, out var job);
        return job;
    }

    public IReadOnlyList<TiaJob> List()
    {
        return jobs.Values
            .OrderByDescending(job => job.CreatedAtUtc)
            .ToList();
    }
}
