import { useCustomerAuth } from "../context/CustomerAuthContext";
import { useNavigation } from "../context/NavigationContext";
import { ASSISTANT_NAME } from "../lib/publicBrand";

export function CompanyHomePage() {
  const { session, welcome } = useCustomerAuth();
  const { openChat, setNav } = useNavigation();
  const actions = welcome?.quick_actions ?? session?.quickActions ?? [];

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>Компания</h1>
        <p>Что происходит сейчас.</p>
      </header>

      <section className="hero">
        <p className="hero__eyebrow">{ASSISTANT_NAME}</p>
        <h1>Добро пожаловать в вашу цифровую компанию</h1>
        <p className="hero__sub">{session?.name}</p>
      </section>

      <section className="card">
        <h2>Начните с Vector</h2>
        <p className="hint">
          Один {ASSISTANT_NAME} для всего: идеи, бизнес, проекты, файлы. Без режимов — просто
          разговор, как с сотрудником.
        </p>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => openChat()}
        >
          Написать {ASSISTANT_NAME}
        </button>
      </section>

      {actions.length > 0 ? (
        <section className="card">
          <h2>Быстрый старт</h2>
          <div className="welcome__actions-grid">
            {actions.map((a) => (
              <button
                key={a.id}
                type="button"
                className="btn btn--ghost welcome__action"
                onClick={() => openChat(a.label)}
              >
                {a.label}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <section className="card card--muted">
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => setNav("projects")}
        >
          Все проекты →
        </button>
      </section>
    </div>
  );
}
