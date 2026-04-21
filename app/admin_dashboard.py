"""FastUI components for admins."""

from __future__ import annotations

from urllib.parse import urljoin

from fastui import AnyComponent, components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from pydantic import BaseModel

from app.components import build_footer, build_navbar
from app.fruger_pages import build_nyc_analytics_embedded_sections
from app.fruger_tailwind import (
    BODY,
    CHART_CAPTION,
    CHART_CARD,
    DATA_TABLE,
    EMPTY_STATE,
    H1,
    H2,
    IMG,
    LINK,
    PAGE,
    STAT_TILE,
    TABLE_SECTION_TITLE,
    TABLE_WRAP,
)

# FastUI prebuilt passes only src/width/height/title/sandbox/srcDoc to <iframe> — no className.
_ADMIN_FLEET_SHELL = (
    "admin-fleet-map-shell w-full max-w-none rounded-md shadow-fruger-float overflow-hidden "
    "border border-fruger-container bg-fruger-surface"
)
from app.schemas.analytics import NycOverviewResponse
from app.schemas.operational import AdminStatsOut, UserPublic

_MUTED = "text-xs font-medium uppercase tracking-wide text-fruger-muted"
_STAT_VALUE = "font-display text-4xl font-extrabold tracking-tight text-fruger-on mt-2"
_STAT_HINT = "text-sm text-fruger-muted mt-2"
_CARD_TITLE = "font-display text-xl font-bold text-fruger-on"
_CARD_BLURB = "text-sm text-fruger-muted mt-1"


class _RidesByStatusRow(BaseModel):
    status: str
    count: int


def _nav_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=LINK,
    )


def _status_label(raw: str) -> str:
    return raw.replace("_", " ").title()


def _stat_tile(*, label: str, value: str, hint: str | None = None) -> AnyComponent:
    inner: list[AnyComponent] = [
        c.Paragraph(text=label, class_name=_MUTED),
        c.Paragraph(text=value, class_name=_STAT_VALUE),
    ]
    if hint:
        inner.append(c.Paragraph(text=hint, class_name=_STAT_HINT))
    return c.Div(class_name=STAT_TILE, components=inner)


def build_admin_dashboard(
    stats: AdminStatsOut,
    user: UserPublic | None = None,
    *,
    nyc_overview: NycOverviewResponse | None = None,
    nyc_error: str | None = None,
    request_base: str | None = None,
) -> list[AnyComponent]:
    rev_dollars = stats.completed_revenue_cents / 100.0
    rev_primary = f"${rev_dollars:,.2f}"
    rev_hint = f"{stats.completed_revenue_cents:,} cents recorded on completed rides"

    status_rows = [
        _RidesByStatusRow(status=_status_label(k), count=v)
        for k, v in sorted(stats.rides_by_status.items())
    ]
    status_section: list[AnyComponent] = [
        c.Heading(
            text="Rides by status",
            level=2,
            class_name=TABLE_SECTION_TITLE,
        ),
    ]
    if status_rows:
        status_section.append(
            c.Div(
                class_name=TABLE_WRAP + " mb-8",
                components=[
                    c.Table(
                        data=status_rows,
                        data_model=_RidesByStatusRow,
                        columns=[
                            DisplayLookup(field="status", title="Status"),
                            DisplayLookup(field="count", title="Rides"),
                        ],
                        class_name=DATA_TABLE,
                    ),
                ],
            )
        )
    else:
        status_section.append(
            c.Div(
                class_name=EMPTY_STATE,
                components=[
                    c.Paragraph(text="No rides in the database yet.", class_name=BODY),
                ],
            )
        )

    components: list[AnyComponent] = [
        build_navbar(user),
        c.Heading(text="Fruger admin", level=1, class_name=H1),
        c.Div(
            class_name="flex flex-wrap gap-3",
            components=[_nav_link("Fruger home", "/")],
        ),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Marketplace rides",
                    value=f"{stats.total_rides:,}",
                    hint="In-app ride requests (SQLite rides table), not the NYC TLC CSV",
                ),
                _stat_tile(
                    label="NYC pickup records",
                    value=f"{stats.nyc_pickup_records:,}",
                    hint="Historical TLC pickup events seeded for analytics only",
                ),
                _stat_tile(
                    label="Total bids",
                    value=f"{stats.total_bids:,}",
                    hint="Driver offers on rides",
                ),
                _stat_tile(
                    label="Completed revenue",
                    value=rev_primary,
                    hint=rev_hint,
                ),
            ],
        ),
        c.Heading(text="Fleet map", level=2, class_name=H2),
        c.Div(
            class_name=CHART_CARD + " w-full max-w-none",
            components=[
                c.Paragraph(
                    text=(
                        "Live driver positions (last reported GPS). "
                        "A Google Maps API key enables the map tiles. Refreshes every 10s."
                    ),
                    class_name=_CARD_BLURB,
                ),
                *(
                    [
                        c.Div(
                            class_name=_ADMIN_FLEET_SHELL,
                            components=[
                                c.Iframe(
                                    src=urljoin(request_base + "/", "embed/admin/map"),
                                    title="Fleet map",
                                    width="100%",
                                )
                            ],
                        )
                    ]
                    if request_base
                    else [
                        c.Paragraph(
                            text="Map embed unavailable (missing request base URL).",
                            class_name=BODY,
                        )
                    ]
                ),
            ],
        ),
        *status_section,
        c.Heading(text="Revenue by day (UTC)", level=2, class_name=H2),
        c.Div(
            class_name=CHART_CARD + " max-w-4xl",
            components=[
                c.Image(
                    src="/api/v1/admin/plots/revenue.png",
                    alt="Revenue by day",
                    class_name=IMG + " w-full rounded-lg",
                ),
                c.Paragraph(
                    text="Completed rides only · USD · UTC midnight boundaries",
                    class_name=CHART_CAPTION,
                ),
            ],
        ),
        *build_nyc_analytics_embedded_sections(
            nyc_overview, nyc_error, request_base=request_base
        ),
        build_footer(),
    ]
    return [c.Page(class_name=PAGE, components=components)]
