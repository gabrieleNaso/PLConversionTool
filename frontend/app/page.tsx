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

type TiaOverview = {
  bridgeConfiguredUrl: string;
  bridgeHealth: {
    status: string;
    service: string;
    mode?: string;
    remoteReachable?: boolean | null;
  };
  bridgeStatus: {
    mode: string;
    supportedOperations: string[];
    remoteTarget?: {
      agentUrl?: string | null;
      host?: string | null;
      port?: string;
      vmwareNetworkMode?: string;
    };
    remoteAgentStatus?: {
      mode?: string;
      tiaPortalVersion?: string;
      detail?: string;
    } | null;
    detail?: string;
  };
};

type ConversionProfile = {
  tia_portal_version: string;
  graph_version: string;
  supported_artifacts: string[];
  recommended_db_sections: string[];
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
  const defaultTiaOverview: TiaOverview = {
    bridgeConfiguredUrl: "http://tia-bridge:8010",
    bridgeHealth: {
      status: "unreachable",
      service: "tia-bridge",
      mode: "unknown",
      remoteReachable: null,
    },
    bridgeStatus: {
      mode: "unknown",
      supportedOperations: [],
      remoteTarget: {
        agentUrl: null,
        host: null,
        port: undefined,
        vmwareNetworkMode: undefined,
      },
      remoteAgentStatus: null,
    },
  };
  const defaultConversionProfile: ConversionProfile = {
    tia_portal_version: "V20",
    graph_version: "GRAPH V2",
    supported_artifacts: [],
    recommended_db_sections: [],
  };

  const health = await fetchJson<HealthStatus>(
    `${internalBackendUrl}/health`,
    defaultHealth,
  );

  const summary = await fetchJson<ProjectSummary>(
    `${internalBackendUrl}/api/project-summary`,
    defaultSummary,
  );
  const tiaOverview = await fetchJson<TiaOverview>(
    `${internalBackendUrl}/api/tia/overview`,
    defaultTiaOverview,
  );
  const conversionProfile = await fetchJson<ConversionProfile>(
    `${internalBackendUrl}/api/conversion/profile`,
    defaultConversionProfile,
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
          <div className="status-card">
            <span className="label">TIA bridge mode</span>
            <strong>{tiaOverview.bridgeStatus.mode}</strong>
          </div>
          <div className="status-card">
            <span className="label">Windows agent reachability</span>
            <strong>
              {tiaOverview.bridgeHealth.remoteReachable === null
                ? "stub / not probed"
                : tiaOverview.bridgeHealth.remoteReachable
                  ? "reachable"
                  : "unreachable"}
            </strong>
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

      <section className="grid">
        <article className="panel">
          <h2>Boundary TIA</h2>
          <ul>
            <li>
              <strong>Bridge URL</strong>
              <span>{tiaOverview.bridgeConfiguredUrl}</span>
            </li>
            <li>
              <strong>Operazioni supportate</strong>
              <span>
                {tiaOverview.bridgeStatus.supportedOperations.length > 0
                  ? tiaOverview.bridgeStatus.supportedOperations.join(", ")
                  : "non ancora disponibili"}
              </span>
            </li>
            <li>
              <strong>Network mode</strong>
              <span>{tiaOverview.bridgeStatus.remoteTarget?.vmwareNetworkMode ?? "n/d"}</span>
            </li>
          </ul>
        </article>

        <article className="panel">
          <h2>Windows Agent</h2>
          <ul>
            <li>
              <strong>Target</strong>
              <span>
                {tiaOverview.bridgeStatus.remoteTarget?.agentUrl ??
                  tiaOverview.bridgeStatus.remoteTarget?.host ??
                  "non configurato"}
              </span>
            </li>
            <li>
              <strong>Remote mode</strong>
              <span>{tiaOverview.bridgeStatus.remoteAgentStatus?.mode ?? "n/d"}</span>
            </li>
            <li>
              <strong>TIA version</strong>
              <span>{tiaOverview.bridgeStatus.remoteAgentStatus?.tiaPortalVersion ?? "n/d"}</span>
            </li>
          </ul>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Core Converter</h2>
          <ul>
            <li>
              <strong>Target TIA</strong>
              <span>{conversionProfile.tia_portal_version}</span>
            </li>
            <li>
              <strong>Profilo GRAPH</strong>
              <span>{conversionProfile.graph_version}</span>
            </li>
            <li>
              <strong>Artefatti previsti</strong>
              <span>
                {conversionProfile.supported_artifacts.length > 0
                  ? conversionProfile.supported_artifacts.join(", ")
                  : "profilo in caricamento"}
              </span>
            </li>
          </ul>
        </article>

        <article className="panel">
          <h2>Companion DB</h2>
          <ul>
            <li>
              <strong>Sezioni consigliate</strong>
              <span>
                {conversionProfile.recommended_db_sections.length > 0
                  ? conversionProfile.recommended_db_sections.join(", ")
                  : "profilo in caricamento"}
              </span>
            </li>
            <li>
              <strong>Bootstrap API</strong>
              <span>
                <code>/api/conversion/bootstrap</code>
              </span>
            </li>
          </ul>
        </article>
      </section>

      <section className="panel">
        <h2>Prossimo passo consigliato</h2>
        <p>
          Implementare il modello intermedio esplicito di stato/transizione nel core
          `src/`, poi collegarlo alla bootstrap API e infine alla generazione XML/import
          verso <code>/api/tia/jobs/import</code>.
        </p>
      </section>
    </main>
  );
}
