import { useState } from "react";
import type { FactoryProduct } from "../lib/endpoints";
import { apiBase } from "../lib/apiClient";
import type { AppSettings } from "../lib/settings";

type ProjectTab = "tasks" | "files" | "deploy" | "history";

type ProjectDetailProps = {
  product: FactoryProduct;
  settings: AppSettings;
  onBack: () => void;
};

function checkLabel(c: FactoryProduct["checks"][0]): string {
  return c.label ?? c.name ?? "Check";
}

function checkOk(c: FactoryProduct["checks"][0]): boolean {
  return Boolean(c.ok ?? c.passed);
}

export function ProjectDetail({ product, settings, onBack }: ProjectDetailProps) {
  const [tab, setTab] = useState<ProjectTab>("tasks");
  const base = apiBase(settings);
  const exportUrl = `${base}/api/factory/products/${product.product_id}/export`;

  return (
    <div className="page page--wide">
      <header className="page__header page__header--row">
        <div>
          <button type="button" className="btn btn--ghost btn--back" onClick={onBack}>
            ← Projects
          </button>
          <h1>{product.business_name}</h1>
          <p>
            {product.status_label} · {product.quality_percent}% · rev {product.revision}
          </p>
        </div>
      </header>

      <div className="tabs" role="tablist">
        {(
          [
            ["tasks", "Tasks"],
            ["files", "Files"],
            ["deploy", "Deploy"],
            ["history", "History"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={`tabs__btn${tab === id ? " is-active" : ""}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "tasks" ? (
        <section className="card">
          <h2>Quality checks</h2>
          {product.checks.length === 0 ? (
            <p className="hint">No checks recorded yet.</p>
          ) : (
            <ul className="task-list">
              {product.checks.map((c, i) => (
                <li key={`${checkLabel(c)}-${i}`}>
                  <span className={checkOk(c) ? "task--ok" : "task--pending"}>
                    {checkOk(c) ? "✓" : "○"}
                  </span>
                  {checkLabel(c)}
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {tab === "files" ? (
        <section className="card">
          <h2>Files & preview</h2>
          <dl className="kv">
            <div>
              <dt>Preview</dt>
              <dd>
                {product.preview_url ? (
                  <a href={product.preview_url} target="_blank" rel="noreferrer">
                    Open preview
                  </a>
                ) : (
                  "—"
                )}
              </dd>
            </div>
            <div>
              <dt>Export bundle</dt>
              <dd>
                <a href={exportUrl} target="_blank" rel="noreferrer">
                  Download export
                </a>
              </dd>
            </div>
          </dl>
        </section>
      ) : null}

      {tab === "deploy" ? (
        <section className="card">
          <h2>Deploy status</h2>
          <dl className="kv">
            <div>
              <dt>Owner approved</dt>
              <dd>{product.owner_approved ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Published</dt>
              <dd>{product.published ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Public URL</dt>
              <dd>
                {product.public_url ? (
                  <a href={product.public_url} target="_blank" rel="noreferrer">
                    {product.public_url}
                  </a>
                ) : (
                  "Not published"
                )}
              </dd>
            </div>
            <div>
              <dt>Delivered</dt>
              <dd>{product.delivered_to_client ? "Yes" : "No"}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      {tab === "history" ? (
        <section className="card">
          <h2>Timeline</h2>
          <ul className="timeline timeline--dense">
            <li>
              <time>Created</time>
              <span>{product.created_at}</span>
            </li>
            <li>
              <time>Updated</time>
              <span>{product.updated_at}</span>
            </li>
            {product.owner_approved_at ? (
              <li>
                <time>Approved</time>
                <span>{product.owner_approved_at}</span>
              </li>
            ) : null}
            {product.published_at ? (
              <li>
                <time>Published</time>
                <span>{product.published_at}</span>
              </li>
            ) : null}
            {product.delivered_at ? (
              <li>
                <time>Delivered</time>
                <span>{product.delivered_at}</span>
              </li>
            ) : null}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
