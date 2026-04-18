"""Matplotlib bar charts (PNG) for NYC pickup breakdowns."""

from __future__ import annotations

import io
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.schemas.analytics import CountByLabel


def _bar_chart_png(labels: Sequence[str], values: Sequence[float], title: str, ylabel: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color="#276ef1")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _rows_to_chart(rows: list[CountByLabel], *, title: str, ylabel: str, max_bars: int) -> bytes:
    slice_ = rows[:max_bars]
    labels = [r.label[:28] + ("…" if len(r.label) > 28 else "") for r in slice_]
    values = [float(r.count) for r in slice_]
    return _bar_chart_png(labels, values, title, ylabel)


def borough_chart_png(rows: list[CountByLabel]) -> bytes:
    return _rows_to_chart(rows, title="Pickups by NYC borough", ylabel="Pickups", max_bars=12)


def base_chart_png(rows: list[CountByLabel]) -> bytes:
    return _rows_to_chart(rows, title="Pickups by TLC base code", ylabel="Pickups", max_bars=10)


def hour_chart_png(rows: list[CountByLabel]) -> bytes:
    return _rows_to_chart(rows, title="Pickups by hour of day", ylabel="Pickups", max_bars=24)


def pickups_by_date_chart_png(rows: list[CountByLabel]) -> bytes:
    slice_ = rows[-40:]
    labels = [r.label[:16] for r in slice_]
    values = [float(r.count) for r in slice_]
    return _bar_chart_png(labels, values, "Pickups by date", "Pickups")
