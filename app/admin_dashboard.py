"""FastUI components for admins."""

from __future__ import annotations

from fastui import AnyComponent, components as c

from app.schemas.operational import AdminStatsOut


def build_admin_dashboard(stats: AdminStatsOut) -> list[AnyComponent]:
    lines = [
        f"Total rides: {stats.total_rides}",
        f"Total bids: {stats.total_bids}",
        f"Completed revenue (cents): {stats.completed_revenue_cents}",
        "By status:",
    ]
    for k, v in sorted(stats.rides_by_status.items()):
        lines.append(f"  {k}: {v}")

    components: list[AnyComponent] = [
        c.Heading(text="Ride-hailing admin", level=1),
        *[c.Text(text=line) for line in lines],
        c.Heading(text="Revenue by day (UTC)", level=2),
        c.Image(src="/api/admin/plots/revenue.png", alt="Revenue", class_name="img-fluid"),
        c.Heading(text="Other", level=2),
        c.Link(href="/api/", text="NYC pickup analytics"),
        c.Text(text=" "),
        c.Link(href="/api/docs", text="API docs"),
    ]
    return [c.Page(components=components)]
