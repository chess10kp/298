"""PNG charts for admin operational metrics."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib import ticker

from app.chart_theme import ACCENT, BAR_PALETTE, finalize_png, style_axes_clean


def revenue_by_day_png(day_revenue: list[tuple[str, int]]) -> bytes:
    """Bar + soft fill for completed revenue per UTC day."""
    fig, ax = plt.subplots(figsize=(10.2, 4.8))
    if not day_revenue:
        ax.set_facecolor("#ffffff")
        ax.text(
            0.5,
            0.5,
            "No completed Fruger rides yet",
            ha="center",
            va="center",
            fontsize=13,
            color="#4c4546",
            transform=ax.transAxes,
        )
        ax.set_axis_off()
        return finalize_png(fig)

    days = [d for d, _ in day_revenue]
    dollars = [c / 100.0 for _, c in day_revenue]
    x = list(range(len(dollars)))
    colors = [BAR_PALETTE[i % len(BAR_PALETTE)] for i in range(len(dollars))]

    ax.bar(
        x,
        dollars,
        color=colors,
        edgecolor="white",
        linewidth=0.9,
        width=0.72,
        zorder=2,
    )
    ax.axhline(0, color="#e4e4e7", linewidth=0.9, zorder=1)

    ax.set_xticks(x)
    ax.set_xticklabels(days, rotation=38, ha="right", fontsize=9)
    ax.set_ylabel("Revenue (USD)", labelpad=8)
    ax.set_xlabel("Day (UTC)", labelpad=8)
    ax.set_title("Fruger marketplace revenue by day", loc="left")
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda v, _: f"${v:,.0f}" if v >= 1000 else f"${v:,.2f}")
    )
    ax.grid(True, axis="y", linestyle="-", alpha=1)
    style_axes_clean(ax)
    return finalize_png(fig)
