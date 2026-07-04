import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { fetchProjects, type FactoryProduct } from "../lib/endpoints";

export function ProjectsPage() {
  const { settings } = useAppSettings();
  const [projects, setProjects] = useState<FactoryProduct[]>([]);
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

  return (
    <div className="page page--wide">
      <header className="page__header page__header--row">
        <div>
          <h1>Projects</h1>
          <p>Factory products from <code>/api/factory/products</code></p>
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
          <p>No factory projects yet. They will appear here when created on the server.</p>
        </section>
      ) : null}

      <div className="project-grid">
        {projects.map((p) => (
          <article key={p.product_id} className="card project-card">
            <div className="project-card__head">
              <h2>{p.business_name}</h2>
              <span className={`badge badge--${p.status}`}>{p.status_label}</span>
            </div>
            <p className="project-card__type">{p.product_type}</p>
            <p className="project-card__desc">{p.description}</p>
            <dl className="kv kv--compact">
              <div>
                <dt>Quality</dt>
                <dd>{p.quality_percent}%</dd>
              </div>
              <div>
                <dt>Approved</dt>
                <dd>{p.owner_approved ? "Yes" : "No"}</dd>
              </div>
              <div>
                <dt>Published</dt>
                <dd>{p.published ? "Yes" : "No"}</dd>
              </div>
            </dl>
            {p.public_url ? (
              <a className="project-card__link" href={p.public_url} target="_blank" rel="noreferrer">
                Open public URL
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}
