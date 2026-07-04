import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useNavigation } from "../context/NavigationContext";
import { ProjectDetail } from "../components/ProjectDetail";
import { fetchProject, fetchProjects, type FactoryProduct } from "../lib/endpoints";

function statusTone(status: string): string {
  if (status.includes("publish") || status.includes("done")) return "done";
  if (status.includes("work") || status.includes("progress")) return "active";
  return "default";
}

export function ProjectsPage() {
  const { settings } = useAppSettings();
  const { projectId, openProject, closeProject } = useNavigation();
  const [projects, setProjects] = useState<FactoryProduct[]>([]);
  const [detail, setDetail] = useState<FactoryProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects(settings);
      setProjects(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [settings]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!projectId) {
      setDetail(null);
      return;
    }
    void fetchProject(settings, projectId)
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [projectId, settings]);

  if (projectId && detail) {
    return (
      <ProjectDetail
        product={detail}
        settings={settings}
        onBack={closeProject}
      />
    );
  }

  return (
    <div className="page page--wide">
      <header className="page__header page__header--row">
        <div>
          <h1>Projects</h1>
          <p>{projects.length} рабочих проектов · factory API</p>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => void load()}
          disabled={loading}
        >
          Refresh
        </button>
      </header>

      {loading ? <p className="hint">Loading projects…</p> : null}
      {error ? <p className="banner banner--warn">{error}</p> : null}

      {!loading && projects.length === 0 ? (
        <section className="card card--muted">
          <p>No projects yet.</p>
        </section>
      ) : null}

      <div className="project-grid">
        {projects.map((p) => (
          <article key={p.product_id} className="card project-card project-card--click">
            <button
              type="button"
              className="project-card__open"
              onClick={() => openProject(p.product_id)}
            >
              <div className="project-card__head">
                <div>
                  <h2>{p.business_name}</h2>
                  <p className="project-card__type">{p.product_type}</p>
                </div>
                <span className={`badge badge--${statusTone(p.status)}`}>
                  {p.status_label}
                </span>
              </div>

              <p className="project-card__desc">{p.description}</p>

              <div className="progress" aria-hidden>
                <div
                  className="progress__bar"
                  style={{ width: `${p.quality_percent}%` }}
                />
              </div>
              <div className="progress__label">
                <span>In progress</span>
                <strong>{p.quality_percent}%</strong>
              </div>
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
