import { useNavigation } from "../context/NavigationContext";
import type { CustomerProject } from "../lib/projectApi";
import { ASSISTANT_NAME } from "../lib/publicBrand";

type Props = {
  project: CustomerProject;
  onBack: () => void;
};

const FOLDER_LABELS: Record<string, string> = {
  website: "Ваш сайт",
  business_plan: "Бизнес-план",
  presentation: "Презентация",
  documents: "Результаты работы",
  images: "Изображения",
  source: "Исходные материалы",
  archive: "Архив",
};

export function CustomerProjectView({ project, onBack }: Props) {
  const { openChat } = useNavigation();
  const identity = project.identity;
  const progress = project.progress;
  const folders = project.artifact_folders ?? [];

  return (
    <div className="page page--wide">
      <header className="page__header page__header--row">
        <div>
          <button type="button" className="btn btn--ghost" onClick={onBack}>
            ← Все проекты
          </button>
          <h1>{identity?.title || project.title}</h1>
          <p className="hint">
            {identity?.type_label || "Проект"} · {identity?.status || "в работе"}
          </p>
        </div>
      </header>

      {progress ? (
        <section className="card card--compact">
          <h2>Прогресс</h2>
          <p>{progress.current_stage_label}</p>
          <div className="progress" aria-hidden>
            <div
              className="progress__bar"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <p className="hint">{progress.percent}% готовности</p>
        </section>
      ) : null}

      {project.next_action?.label || project.next_step_hint ? (
        <section className="card">
          <h2>Что делать дальше</h2>
          <p>{project.next_action?.label || project.next_step_hint}</p>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() =>
              openChat(project.next_action?.label || project.next_step_hint)
            }
          >
            Написать {ASSISTANT_NAME}
          </button>
        </section>
      ) : null}

      {folders.length > 0 ? (
        <section className="card">
          <h2>Результаты работы</h2>
          {folders.map((folder) => (
            <div key={folder.id} className="project-folder">
              <h3>
                {FOLDER_LABELS[folder.id] ?? folder.label} ({folder.count})
              </h3>
              {folder.items.length === 0 ? (
                <p className="hint">Пока пусто — {ASSISTANT_NAME} добавит после работы.</p>
              ) : (
                <ul className="link-list">
                  {folder.items.map((item) => (
                    <li key={item.label}>
                      {item.href ? (
                        <a href={item.href} target="_blank" rel="noreferrer">
                          {item.label}
                        </a>
                      ) : (
                        <span>{item.label}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </section>
      ) : null}

      {project.timeline && project.timeline.length > 0 ? (
        <section className="card">
          <h2>История</h2>
          <ul className="timeline timeline--dense">
            {project.timeline.slice(0, 8).map((ev, i) => (
              <li key={`${ev.at}-${i}`}>
                <time>{ev.at}</time>
                <span>
                  {ev.label}
                  {ev.detail ? ` — ${ev.detail}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
