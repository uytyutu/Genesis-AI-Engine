import { ASSISTANT_NAME } from "../lib/publicBrand";

type Props = {
  connected: boolean;
  thinking?: boolean;
  compact?: boolean;
};

export function VectorStatus({ connected, thinking = false, compact = false }: Props) {
  const detail = !connected
    ? "недоступен"
    : thinking
      ? "думает…"
      : compact
        ? "на связи"
        : "ведёт вашу компанию";

  return (
    <div
      className={`vector-status${connected ? " vector-status--online" : ""}${thinking ? " vector-status--busy" : ""}`}
      role="status"
      aria-live="polite"
    >
      <span className="vector-status__dot" aria-hidden />
      <span className="vector-status__text">
        <strong>{ASSISTANT_NAME}</strong>
        <span className="vector-status__detail">{detail}</span>
      </span>
    </div>
  );
}
