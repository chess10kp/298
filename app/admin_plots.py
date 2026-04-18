"""PNG charts for admin operational metrics."""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def revenue_by_day_png(day_revenue: list[tuple[str, int]]) -> bytes:
    """Bar chart of revenue cents per day."""
    fig, ax = plt.subplots(figsize=(8, 4))
    if not day_revenue:
        ax.text(0.5, 0.5, "No completed rides yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        days = [d for d, _ in day_revenue]
        cents = [c / 100.0 for _, c in day_revenue]
        ax.bar(days, cents, color="#2563eb")
        ax.set_ylabel("Revenue ($)")
        ax.set_xlabel("Day (UTC)")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()
