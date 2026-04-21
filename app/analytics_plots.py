"""Matplotlib charts (PNG) for NYC pickup breakdowns — Fruger visual system."""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt

from app.chart_theme import (
    ACCENT,
    BAR_PALETTE,
    finalize_png,
    style_axes_clean,
)
from app.schemas.analytics import CountByLabel


def _bar_colors(n: int) -> list[str]:
    return [BAR_PALETTE[i % len(BAR_PALETTE)] for i in range(n)]


def _horizontal_bars_png(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str,
    xlabel: str,
    fig_width: float = 10.0,
) -> bytes:
    n = len(labels)
    fig_h = max(3.6, min(16.0, 0.5 * n + 2.2))
    fig, ax = plt.subplots(figsize=(fig_width, fig_h))
    y_pos = list(range(n))
    ax.barh(
        y_pos,
        list(values),
        height=0.65,
        color=_bar_colors(n),
        edgecolor="white",
        linewidth=0.85,
        zorder=2,
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(labels), fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_title(title, loc="left")
    ax.grid(True, axis="x", linestyle="-", alpha=1)
    style_axes_clean(ax)
    return finalize_png(fig)


def _line_series_png(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str,
    ylabel: str,
    marker_every: int | None = None,
) -> bytes:
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    x = list(range(len(values)))
    ax.fill_between(x, values, alpha=0.14, color=ACCENT, zorder=1)
    ax.plot(
        x,
        values,
        color=ACCENT,
        linewidth=2.4,
        marker="o",
        markersize=5,
        markerfacecolor="white",
        markeredgewidth=1.6,
        markeredgecolor=ACCENT,
        zorder=3,
        markevery=marker_every,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(list(labels), rotation=42, ha="right", fontsize=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.set_title(title, loc="left")
    ax.grid(True, axis="y", linestyle="-", alpha=1)
    style_axes_clean(ax)
    return finalize_png(fig)


def _rows_horizontal(rows: list[CountByLabel], *, title: str, xlabel: str, max_bars: int) -> bytes:
    slice_ = rows[:max_bars]
    labels = [r.label[:34] + ("…" if len(r.label) > 34 else "") for r in slice_]
    values = [float(r.count) for r in slice_]
    return _horizontal_bars_png(labels, values, title=title, xlabel=xlabel)


def borough_chart_png(rows: list[CountByLabel]) -> bytes:
    return _rows_horizontal(
        rows, title="Pickups by NYC borough", xlabel="Pickups", max_bars=14
    )


def base_chart_png(rows: list[CountByLabel]) -> bytes:
    return _rows_horizontal(
        rows, title="Pickups by TLC base code", xlabel="Pickups", max_bars=12
    )


def hour_chart_png(rows: list[CountByLabel]) -> bytes:
    slice_ = rows[:24]
    labels = [r.label for r in slice_]
    values = [float(r.count) for r in slice_]
    n = len(values)
    every = 1 if n <= 16 else max(1, n // 16)
    return _line_series_png(
        labels,
        values,
        title="Pickups by hour of day",
        ylabel="Pickups",
        marker_every=every,
    )


def pickups_by_date_chart_png(rows: list[CountByLabel]) -> bytes:
    slice_ = rows[-48:]
    labels = [r.label[:14] for r in slice_]
    values = [float(r.count) for r in slice_]
    n = len(values)
    every = 1 if n <= 20 else max(1, n // 20)
    return _line_series_png(
        labels,
        values,
        title="Pickups by date",
        ylabel="Pickups",
        marker_every=every,
    )
