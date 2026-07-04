import { useEffect } from "react";
import { useSession } from "../context/SessionContext";
import { checkForUpdates } from "../lib/updater";
import { useAppSettings } from "../context/AppSettingsContext";

export function HomePage() {
  const { settings } = useAppSettings();
  const { dashboard, ownerLabel, refresh, systemVersion, error } = useSession();

  useEffect(() => {
    void refresh();
    if (settings.checkUpdatesOnLaunch) {
      void checkForUpdates(true);
    }
  }, [refresh, settings.checkUpdatesOnLaunch]);

  if (!dashboard) {
    return (
      <div className="page">
        <p className="hint">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>{dashboard.greeting}</h1>
        <p>
          {ownerLabel} · Genesis {systemVersion ?? "—"} · {dashboard.uptime_label}
        </p>
      </header>

      {error ? <p className="banner banner--warn">{error}</p> : null}

      <div className="stat-grid">
        <article className="stat">
          <span className="stat__label">Projects</span>
          <strong className="stat__value">{dashboard.products_count}</strong>
        </article>
        <article className="stat">
          <span className="stat__label">Queue</span>
          <strong className="stat__value">{dashboard.queue_pending}</strong>
        </article>
        <article className="stat">
          <span className="stat__label">Revenue today</span>
          <strong className="stat__value">
            €{dashboard.revenue_today_eur.toFixed(2)}
          </strong>
        </article>
        <article className="stat">
          <span className="stat__label">System load</span>
          <strong className="stat__value">{dashboard.system_load_percent}%</strong>
        </article>
      </div>

      <section className="card">
        <h2>Today</h2>
        <p className="goal">{dashboard.daily_goal}</p>
        <p className="hint">{dashboard.tip}</p>
      </section>

      <section className="card">
        <h2>Services</h2>
        <ul className="list-plain">
          {dashboard.services_summary.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </section>

      {dashboard.recent_events.length > 0 ? (
        <section className="card">
          <h2>Recent activity</h2>
          <ul className="timeline">
            {dashboard.recent_events.slice(0, 6).map((ev, i) => (
              <li key={`${ev.icon}-${ev.message}-${i}`}>
                <span aria-hidden>{ev.icon}</span>
                <span>{ev.message}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
