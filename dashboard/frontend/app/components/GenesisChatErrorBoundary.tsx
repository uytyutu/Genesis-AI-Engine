"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

type Props = { children: ReactNode; publicMode?: boolean };
type State = { error: Error | null };

export class GenesisChatErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Vector panel error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-2xl border border-rose-500/30 bg-genesis-panel p-6 text-sm">
          <p className="font-semibold text-rose-300">
            Не удалось загрузить панель {ASSISTANT_NAME}
          </p>
          <p className="mt-2 text-genesis-muted">
            {this.props.publicMode
              ? `Обновите страницу. Если ошибка повторяется — перезапустите ${BRAND_NAME} с рабочего стола.`
              : `Обновите страницу. Если ошибка повторяется — перезапустите ${BRAND_NAME} или frontend (npm run dev).`}
          </p>
          <button
            type="button"
            className="mt-4 rounded-xl bg-genesis-accent px-4 py-2 text-xs font-semibold text-white"
            onClick={() => this.setState({ error: null })}
          >
            Попробовать снова
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
