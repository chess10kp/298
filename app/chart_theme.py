"""Matplotlib look-and-feel aligned with Fruger ``theme.css`` (PNG exports)."""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

FIG_FACE = "#f4f4f5"
AX_FACE = "#ffffff"
TEXT_PRIMARY = "#1a1c1c"
TEXT_MUTED = "#4c4546"
ACCENT = "#0054cb"
GRID = "#e4e4e7"

# Harmonious blues / slate for categorical bars (long enough for 12+ categories).
BAR_PALETTE = [
    "#0054cb",
    "#1565e6",
    "#2476f0",
    "#3d8ef5",
    "#5aa3f7",
    "#7eb8fa",
    "#1e40af",
    "#1d4ed8",
    "#4f46e5",
    "#6366f1",
    "#64748b",
    "#475569",
]


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": FIG_FACE,
            "axes.facecolor": AX_FACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_MUTED,
            "axes.titlecolor": TEXT_PRIMARY,
            "axes.linewidth": 0.8,
            "text.color": TEXT_PRIMARY,
            "xtick.color": TEXT_MUTED,
            "ytick.color": TEXT_MUTED,
            "grid.color": GRID,
            "grid.linestyle": "-",
            "grid.linewidth": 0.9,
            "grid.alpha": 1.0,
            "font.family": "sans-serif",
            "font.sans-serif": [
                "DejaVu Sans",
                "Liberation Sans",
                "Helvetica Neue",
                "Arial",
                "sans-serif",
            ],
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.titleweight": "600",
            "axes.labelsize": 10,
            "axes.titlepad": 14,
            "figure.dpi": 96,
        }
    )


configure_matplotlib()


def style_axes_clean(ax) -> None:
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)


def finalize_png(fig) -> bytes:
    fig.tight_layout(pad=1.15)
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=144,
        facecolor=FIG_FACE,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.18,
    )
    plt.close(fig)
    buf.seek(0)
    return buf.read()
