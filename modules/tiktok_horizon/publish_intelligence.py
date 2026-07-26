"""Publish Intelligence — timing recommendations with confidence (not virality)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from modules.tiktok_horizon.models import PublishWindow


class PublishIntelligence:
    def recommend(
        self,
        *,
        draft: dict[str, Any],
        analytics_rows: list[dict[str, Any]] | None = None,
        account_stats: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> PublishWindow:
        now = now or datetime.now(timezone.utc)
        analytics_rows = analytics_rows or []
        account_stats = account_stats or {}

        # Prefer historically strong local hours from past posts (when available)
        hour_scores: dict[int, list[float]] = defaultdict(list)
        for row in analytics_rows:
            published_at = row.get("published_at") or row.get("queued_at")
            metric = float(row.get("watch_proxy") or row.get("views") or row.get("engagement") or 0)
            if not published_at:
                continue
            try:
                dt = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
            except ValueError:
                continue
            hour_scores[dt.hour].append(metric)

        reasons: list[str] = []
        best_hour = 18
        confidence = 0.55

        if hour_scores:
            best_hour = max(
                hour_scores.keys(),
                key=lambda h: sum(hour_scores[h]) / max(len(hour_scores[h]), 1),
            )
            confidence = min(0.9, 0.55 + 0.05 * min(len(analytics_rows), 8))
            reasons.append(
                f"похожие публикации ранее показывали лучшие результаты около {best_hour:02d}:00"
            )
        else:
            reasons.append(
                "пока мало истории аккаунта — используется осторожное вечернее окно по умолчанию"
            )

        audience_peak = account_stats.get("peak_hour_local")
        if audience_peak is not None:
            try:
                peak = int(audience_peak)
                best_hour = peak
                confidence = min(0.92, confidence + 0.08)
                reasons.append("в это время аудитория аккаунта была наиболее активна")
            except (TypeError, ValueError):
                pass

        style = (draft.get("style_variant") or (draft.get("script") or {}).get("style_variant") or "")
        if style:
            reasons.append(f"учтён формат ролика ({style})")

        # Local wall-clock window (UTC labeled for Stage 1; locale TZ later)
        start = now.replace(minute=0, second=0, microsecond=0)
        if start.hour > best_hour or (start.hour == best_hour and now.minute > 0):
            start = start + timedelta(days=1)
        start = start.replace(hour=best_hour, minute=30 if best_hour == 18 else 0)
        end = start + timedelta(hours=1, minutes=30)

        label = "High" if confidence >= 0.8 else "Medium" if confidence >= 0.65 else "Low"
        return PublishWindow(
            window_start_local=start.isoformat(),
            window_end_local=end.isoformat(),
            confidence=round(confidence, 2),
            confidence_label=label,
            reasons=reasons[:5],
        )
