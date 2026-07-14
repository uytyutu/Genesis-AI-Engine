import { useState } from "react";
import { useCustomerAuth } from "../context/CustomerAuthContext";
import { GenesisMark } from "../components/GenesisMark";
import { BRAND_NAME } from "../lib/publicBrand";

export function RegisterPage() {
  const { register, login, busy, error } = useCustomerAuth();
  const [mode, setMode] = useState<"register" | "login">("register");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function onSubmit() {
    if (mode === "register") {
      await register(name, email, password);
    } else {
      await login(email, password);
    }
  }

  return (
    <div className="connect">
      <div className="connect__card connect__card--wide">
        <div className="connect__logo" aria-hidden>
          <GenesisMark className="connect__logo-svg" />
        </div>
        <h1>
          {mode === "register"
            ? "Создайте свою цифровую компанию"
            : "С возвращением"}
        </h1>
        <p className="connect__lead">
          {mode === "register"
            ? `${BRAND_NAME} — ваша компания с Vector. Только имя, email и пароль.`
            : "Войдите — ваша компания ждёт на любом устройстве."}
        </p>

        {mode === "register" ? (
          <label className="field">
            <span>Имя</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Как к вам обращаться"
              autoComplete="name"
            />
          </label>
        ) : null}

        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
          />
        </label>

        <label className="field">
          <span>Пароль</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="минимум 8 символов"
            autoComplete={
              mode === "register" ? "new-password" : "current-password"
            }
          />
        </label>

        {error ? (
          <p className="connect__error" role="alert">
            {error}
          </p>
        ) : null}

        <button
          type="button"
          className="btn btn--primary connect__submit"
          disabled={busy}
          onClick={() => void onSubmit()}
        >
          {busy
            ? "Подождите…"
            : mode === "register"
              ? "Создать компанию"
              : "Войти"}
        </button>

        <p className="connect__switch">
          {mode === "register" ? (
            <>
              Уже есть компания?{" "}
              <button
                type="button"
                className="btn btn--link"
                onClick={() => setMode("login")}
              >
                Войти
              </button>
            </>
          ) : (
            <>
              Впервые здесь?{" "}
              <button
                type="button"
                className="btn btn--link"
                onClick={() => setMode("register")}
              >
                Создать компанию
              </button>
            </>
          )}
        </p>

        <p className="connect__hint">
          Google и Apple — скоро. Сейчас: email и пароль.
        </p>
      </div>
    </div>
  );
}
