"""FastUI components for admins."""

from __future__ import annotations

from fastui import AnyComponent, components as c
from fastui.events import GoToEvent

from app.fruger_tailwind import H1, H2, IMG, LINK, PAGE_NARROW as PAGE
from app.schemas.operational import AdminStatsOut

_BODY = "text-fruger-on font-mono text-sm leading-relaxed"


def _nav_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=LINK,
    )


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
        c.Heading(text="Fruger admin", level=1, class_name=H1),
        c.Div(
            class_name="flex flex-wrap gap-3",
            components=[_nav_link("Fruger home", "/")],
        ),
        c.Div(
            class_name="rounded-md bg-fruger-panel p-4 shadow-fruger-float space-y-1",
            components=[c.Paragraph(text=line, class_name=_BODY) for line in lines],
        ),
        c.Heading(text="Revenue by day (UTC)", level=2, class_name=H2),
        c.Image(
            src="/api/admin/plots/revenue.png",
            alt="Revenue",
            class_name=IMG,
        ),
        c.Heading(text="Fleet map", level=2, class_name=H2),
        c.Paragraph(
            text="Live driver positions (last reported GPS) on a map. Requires GOOGLE_MAPS_API_KEY.",
            class_name="text-fruger-muted",
        ),
        _nav_link("Open partner / fleet map", "/admin/map"),
        c.Heading(text="Other", level=2, class_name=H2),
        c.Div(
            class_name="flex flex-wrap gap-4",
            components=[
                _nav_link("NYC pickup analytics", "/analytics"),
                _nav_link("API docs", "/api/docs"),
            ],
        ),
    ]
    return [c.Page(class_name=PAGE, components=components)]
