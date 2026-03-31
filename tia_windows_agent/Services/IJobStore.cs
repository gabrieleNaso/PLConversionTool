using PLConversionTool.TiaAgent.Models;

namespace PLConversionTool.TiaAgent.Services;

public interface IJobStore
{
    void Add(TiaJob job);

    TiaJob Update(
        string jobId,
        Func<TiaJob, TiaJob> update
    );

    TiaJob? Get(string jobId);

    IReadOnlyList<TiaJob> List();
}
