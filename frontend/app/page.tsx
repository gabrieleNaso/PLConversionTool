type ProjectSummary = {
  project: string;
  objective: string;
  targets: string[];
  repositoryAreas: Array<{ name: string; purpose: string }>;
};

type HealthStatus = {
  status: string;
  service: string;
  project: string;
};

async function fetchJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return fallback;
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export default async function Page() {
  const internalBackendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const publicBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  const defaultHealth: HealthStatus = {
    status: "unreachable",
    service: "backend",
    project: "PLConversionTool",
  };
  const defaultSummary: ProjectSummary = {
    project: "PLConversionTool",
    objective: "Convertire sequenziatori PLC AWL in blocchi GRAPH XML importabili.",
    targets: ["TIA Portal V20", "GRAPH V2", "GlobalDB companion", "FC LAD di supporto"],
    repositoryAreas: [],
  };

  const health = await fetchJson<HealthStatus>(
    `${internalBackendUrl}/health`,
    defaultHealth,
  );

  const summary = await fetchJson<ProjectSummary>(
    `${internalBackendUrl}/api/project-summary`,
    defaultSummary,
  );

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">PLC AWL to GRAPH XML</p>
        <h1>{summary.project}</h1>
        <p className="lead">{summary.objective}</p>
        <div className="status-row">
          <div className="status-card">
            <span className="label">Backend status</span>
            <strong>{health.status}</strong>
          </div>
          <div className="status-card">
            <span className="label">Backend URL browser</span>
            <strong>{publicBackendUrl}</strong>
          </div>
        </div>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Target tecnico</h2>
          <ul>
            {summary.targets.map((target) => (
              <li key={target}>{target}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>Aree repository</h2>
          <ul>
            {summary.repositoryAreas.map((area) => (
              <li key={area.name}>
                <strong>{area.name}</strong>
                <span>{area.purpose}</span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel">
        <h2>Prossimo passo consigliato</h2>
        <p>
          Consolidare il modello intermedio del sequenziatore in <code>src/</code> e
          farlo diventare la base comune per parser AWL, generatori XML e validator.
        </p>
      </section>
    </main>
  );
}
