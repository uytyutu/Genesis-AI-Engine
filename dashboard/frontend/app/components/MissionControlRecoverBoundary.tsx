"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { BRAND_NAME } from "../lib/publicBrand";

type Props = { children: ReactNode };
type State = { error: Error | null; retryAt: number };

/**
 * Soft recover for Mission Control home — render crashes must not stick on error.tsx.
 * Auto-retries without a full page reload when backend/UI race after long sessions.
 */
export class MissionControlRecoverBoundary extends Component<Props, State> {
  state: State = { error: null, retryAt: 0 };
  private timer: number | null = null;

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error, retryAt: Date.now() + 3_000 };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Mission Control recover:", error, info);
  }

  componentDidUpdate(_: Props, prev: State) {
    if (this.state.error && !prev.error) {
      this.scheduleRetry();
    }
    if (!this.state.error && prev.error && this.timer != null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
  }

  componentWillUnmount() {
    if (this.timer != null) window.clearTimeout(this.timer);
  }

  private scheduleRetry = () => {
    if (this.timer != null) window.clearTimeout(this.timer);
    this.timer = window.setTimeout(() => {
      this.setState({ error: null, retryAt: 0 });
    }, 3_000);
  };

  private retryNow = () => {
    if (this.timer != null) window.clearTimeout(this.timer);
    this.timer = null;
    this.setState({ error: null, retryAt: 0 });
  };

  render() {
    if (this.state.error) {
      return (
        <main className="mx-auto max-w-lg px-4 py-16 text-center">
          <p className="text-sm font-semibold text-amber-200">Пульт переподключается…</p>
          <p className="mt-2 text-xs text-genesis-muted">
            Сессия долгая или backend на мгновение недоступен. {BRAND_NAME} сам повторит через
            несколько секунд — страницу обновлять не нужно.
          </p>
          <button
            type="button"
            onClick={this.retryNow}
            className="mt-6 rounded-xl border border-emerald-500/40 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-100 hover:bg-emerald-950/50"
          >
            Повторить сейчас
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}
