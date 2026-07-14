import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useCustomerAuth } from "../context/CustomerAuthContext";
import { useNavigation } from "../context/NavigationContext";
import { CustomerProjectView } from "../components/CustomerProjectView";
import { ProjectDetail } from "../components/ProjectDetail";
import {
  fetchCustomerProject,
  type CustomerProject,
  type ProjectPlatformState,
} from "../lib/projectApi";
import { fetchProject, fetchProjects, type FactoryProduct } from "../lib/endpoints";
import { ASSISTANT_NAME } from "../lib/publicBrand";

function DevProjectsPage() {
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
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
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
      <ProjectDetail product={detail} settings={settings} onBack={closeProject} />
    );
  }

  return (
    <div className="page page--wide">
      <header className="page__header page__header--row">
        <div>
          <h1>Projects (dev)</h1>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => void load()}
          disabled={loading}
        >
          Обновить
        </button>
      </header>
      {loading ? <p className="hint">Загрузка…</p> : null}
      {error ? <p className="banner banner--warn">{error}</p> : null}
      <div className="project-grid">
        {projects.map((p) => (
          <article key={p.product_id} className="card project-card project-card--click">
            <button
              type="button"
              className="project-card__open"
              onClick={() => openProject(p.product_id)}
            >
              <h2>{p.business_name}</h2>
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}

function CustomerProjectsPage() {
  const { settings } = useAppSettings();
  const { session } = useCustomerAuth();
  const { openChat } = useNavigation();
  const [state, setState] = useState<ProjectPlatformState | null>(null);
  const [selected, setSelected] = useState<CustomerProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const vid = session?.platformVisitorId ?? "";

  const load = useCallback(async () => {
    if (!vid) {
      setError("Войдите в компанию, чтобы увидеть проекты.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCustomerProject(settings, vid);
      setState(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить проекты");
    } finally {
      setLoading(false);
    }
  }, [settings, vid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (selected) {
    return (
      <CustomerProjectView project={selected} onBack={() => setSelected(null)} />
    );
  }

  const project = state?.project;

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>Проекты</h1>
        <p>Ваши результаты и работа с {ASSISTANT_NAME}.</p>
      </header>

      {loading ? <p className="hint">Загрузка…</p> : null}
      {error ? <p className="banner banner--warn">{error}</p> : null}

      {!loading && !error && !project ? (
        <section className="card card--muted">
          <h2>Пока нет проектов</h2>
          <p className="hint">
            Начните с {ASSISTANT_NAME} — он создаст первый проект вместе с вами.
          </p>
          <button type="button" className="btn btn--primary" onClick={() => openChat()}>
            Написать {ASSISTANT_NAME}
          </button>
        </section>
      ) : null}

      {project ? (
        <article className="card project-card project-card--click">
          <button
            type="button"
            className="project-card__open"
            onClick={() => setSelected(project)}
          >
            <div className="project-card__head">
              <div>
                <h2>{project.identity?.title || project.title}</h2>
                <p className="project-card__type">
                  {project.identity?.type_label || "Проект"}
                </p>
              </div>
              <span className="badge">
                {project.health?.emoji} {project.health?.label || "в работе"}
              </span>
            </div>
            <p className="project-card__desc">
              {project.identity?.description ||
                project.description ||
                project.next_step_hint ||
                "Продолжайте вместе с Vector."}
            </p>
            {project.progress ? (
              <>
                <div className="progress" aria-hidden>
                  <div
                    className="progress__bar"
                    style={{ width: `${project.progress.percent}%` }}
                  />
                </div>
                <div className="progress__label">
                  <span>{project.progress.current_stage_label}</span>
                  <strong>{project.progress.percent}%</strong>
                </div>
              </>
            ) : null}
          </button>
        </article>
      ) : null}

      {state?.vector_hint ? (
        <p className="hint" style={{ marginTop: "1rem" }}>
          {state.vector_hint}
        </p>
      ) : null}
    </div>
  );
}

export function ProjectsPage() {
  const { settings } = useAppSettings();
  if (settings.devMode) {
    return <DevProjectsPage />;
  }
  return <CustomerProjectsPage />;
}
