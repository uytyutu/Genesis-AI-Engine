import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useNavigation } from "../context/NavigationContext";
import { useSession } from "../context/SessionContext";
import {
  fetchActivity,
  fetchModules,
  fetchNotifications,
  fetchProjects,
  type FactoryProduct,
  type ModuleStatus,
  type OwnerNotification,
} from "../lib/endpoints";
import { recentChatSnippet } from "../lib/chatStore";
import { apiBase } from "../lib/apiClient";
import { useI18n } from "../i18n/I18nProvider";

export function HomePage() {
  const { t } = useI18n();
  const { settings } = useAppSettings();
  const { dashboard, ownerLabel, refresh, systemVersion, error, connected } =
    useSession();
  const { openProject, openChat, setNav } = useNavigation();

  const [modules, setModules] = useState<ModuleStatus[]>([]);
  const [notifications, setNotifications] = useState<OwnerNotification[]>([]);
  const [recentProjects, setRecentProjects] = useState<FactoryProduct[]>([]);
  const [activity, setActivity] = useState<{ at: string; message: string }[]>(
    [],
  );
  const [recentMessages] = useState(() => recentChatSnippet(4));

  const loadExtras = useCallback(async () => {
    try {
      const [mods, notes, projects, events] = await Promise.all([
        fetchModules(settings),
        fetchNotifications(settings),
        fetchProjects(settings),
        fetchActivity(settings, 8),
      ]);
      setModules(mods);
      setNotifications(notes.slice(0, 6));
      setRecentProjects(projects.slice(0, 4));
      setActivity(events);
    } catch {
      /* home still shows dashboard */
    }
  }, [settings]);

  useEffect(() => {
    void refresh();
    void loadExtras();
  }, [refresh, loadExtras]);

  if (!dashboard) {
    return (
      <div className="page">
        <p className="hint">{t("boot.loading")}</p>
      </div>
    );
  }

  const alertCount =
    dashboard.queue_pending +
    dashboard.errors_today +
    notifications.filter((n) => !n.read).length;

  return (
    <div className="page page--wide">
      <section className="hero">
        <p className="hero__eyebrow">{t("home.welcome")}</p>
        <h1>{dashboard.greeting}</h1>
        <p className="hero__sub">
          {ownerLabel} · Genesis {systemVersion ?? "—"} · {dashboard.uptime_label}
        </p>
        <div
          className={`hero__status${dashboard.system_running ? " is-ok" : ""}`}
        >
          {dashboard.system_running && dashboard.all_services_ok
            ? t("home.ready")
            : t("home.attention")}
        </div>
      </section>

      {error ? <p className="banner banner--warn">{error}</p> : null}

      <section className="card">
        <h2>Инфраструктура</h2>
        <dl className="kv kv--infra">
          <div>
            <dt>API</dt>
            <dd className={connected ? "text-ok" : "text-warn"}>
              {connected ? "Online" : "Offline"} · {apiBase(settings)}
            </dd>
          </div>
          <div>
            <dt>Railway / modules</dt>
            <dd>
              {modules.length === 0 ? (
                "Loading…"
              ) : (
                <ul className="module-list">
                  {modules.map((m) => (
                    <li key={m.id}>
                      <span className={`dot dot--${m.status}`} aria-hidden />
                      {m.label}: {m.status}
                    </li>
                  ))}
                </ul>
              )}
            </dd>
          </div>
        </dl>
      </section>

      <section className="today">
        <h2 className="section-title">Сегодня</h2>
        <div className="stat-grid">
          <article className="stat">
            <span className="stat__label">Проекты</span>
            <strong className="stat__value">{dashboard.products_count}</strong>
            <span className="stat__sub">
              +{dashboard.products_created_today} сегодня
            </span>
          </article>
          <article className="stat">
            <span className="stat__label">Уведомления</span>
            <strong className="stat__value">{alertCount}</strong>
            <span className="stat__sub">
              {notifications.filter((n) => !n.read).length} новых
            </span>
          </article>
          <article className="stat">
            <span className="stat__label">Выручка</span>
            <strong className="stat__value">
              €{dashboard.revenue_today_eur.toFixed(0)}
            </strong>
            <span className="stat__sub">
              €{dashboard.revenue_month_eur.toFixed(0)} / мес
            </span>
          </article>
          <article className="stat">
            <span className="stat__label">Нагрузка</span>
            <strong className="stat__value">{dashboard.system_load_percent}%</strong>
            <span className="stat__sub">
              {dashboard.tasks_completed_today} задач
            </span>
          </article>
        </div>
      </section>

      <div className="home-columns">
        <section className="card">
          <div className="card__head">
            <h2>Последние проекты</h2>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => setNav("projects")}
              disabled={recentProjects.length === 0}
            >
              Все
            </button>
          </div>
          {recentProjects.length === 0 ? (
            <p className="hint">Нет проектов на сервере.</p>
          ) : (
            <ul className="link-list">
              {recentProjects.map((p) => (
                <li key={p.product_id}>
                  <button
                    type="button"
                    className="link-list__btn"
                    onClick={() => openProject(p.product_id)}
                  >
                    <strong>{p.business_name}</strong>
                    <span>{p.status_label} · {p.quality_percent}%</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card__head">
            <h2>Последние сообщения</h2>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => openChat()}
            >
              Чат
            </button>
          </div>
          {recentMessages.length === 0 ? (
            <p className="hint">Спросите Genesis в чате.</p>
          ) : (
            <ul className="link-list">
              {recentMessages.map((m, i) => (
                <li key={`${m.at}-${i}`}>
                  <button
                    type="button"
                    className="link-list__btn"
                    onClick={() => openChat(m.text)}
                  >
                    <span className="link-list__time">{m.at}</span>
                    <span>{m.text}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {notifications.length > 0 ? (
        <section className="card">
          <h2>Системные уведомления</h2>
          <ul className="notify-list">
            {notifications.map((n) => (
              <li key={`${n.at}-${n.title}`} className={n.read ? "" : "is-new"}>
                <strong>{n.title}</strong>
                <span>{n.message}</span>
                <time>{n.at}</time>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="card">
        <h2>Фокус дня</h2>
        <p className="goal">{dashboard.daily_goal}</p>
        <p className="hint">{dashboard.tip}</p>
      </section>

      {activity.length > 0 ? (
        <section className="card">
          <h2>Последние действия</h2>
          <ul className="timeline timeline--dense">
            {activity.map((ev, i) => (
              <li key={`${ev.at}-${i}`}>
                <time>{ev.at}</time>
                <span>{ev.message}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {dashboard.recent_events.length > 0 ? (
        <section className="card">
          <h2>События владельца</h2>
          <ul className="timeline">
            {dashboard.recent_events.slice(0, 6).map((ev, i) => (
              <li key={`${ev.icon}-${ev.message}-${i}`}>
                <span className="timeline__icon" aria-hidden>
                  {ev.icon}
                </span>
                <span>{ev.message}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
