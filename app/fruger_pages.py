"""FastUI page trees for Fruger (replaces Jinja templates)."""

from __future__ import annotations

from urllib.parse import urljoin

from fastui import AnyComponent
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from app.components import build_chart_gallery, build_footer, build_navbar
from app.fruger_tailwind import (
    BODY,
    BREAKDOWN_HEADING,
    CARD,
    DATA_TABLE,
    H1,
    H2,
    HERO,
    IFRAME,
    IFRAME_DRIVER,
    IMG,
    PAGE_DRIVER,
    LINK,
    OUTLINE_BTN,
    PAGE,
    STAT_TILE,
    TABLE_SECTION_TITLE,
    TABLE_WRAP,
    WARN_SOFT,
)
from app.schemas.analytics import NycOverviewResponse
from app.schemas.operational import UserPublic, UserRole

_CARD_TITLE = "font-display text-xl font-bold text-fruger-on"
_CARD_BLURB = "text-sm text-fruger-muted mt-1"
_CARD_CTA = "text-xs font-bold uppercase tracking-wide text-fruger-accent mt-3"


def _link_label(text: str, url: str, class_name: str | None = None) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=class_name or LINK,
    )


def _full_navigation_url(request_base: str | None, path: str) -> str:
    """SPA ``GoToEvent`` relative paths become ``/api`` + path and break PNG/JSON GETs."""
    if request_base and path.startswith("/"):
        return f"{request_base.rstrip('/')}{path}"
    return path


def _outline_link(
    text: str,
    url: str,
    *,
    request_base: str | None = None,
    new_tab: bool = False,
) -> AnyComponent:
    """Open JSON or static assets via full document load (not FastUI JSON fetch)."""
    href = _full_navigation_url(request_base, url)
    evt = (
        GoToEvent(url=href, target="_blank")
        if new_tab
        else GoToEvent(url=href)
    )
    return c.Link(
        components=[c.Text(text=text)],
        on_click=evt,
        class_name=OUTLINE_BTN,
    )


def build_api_home_guest(user: UserPublic | None = None) -> list[AnyComponent]:
    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Fruger"),
                build_navbar(user),
                c.Heading(text="Fruger", level=1, class_name=H1),
                c.Paragraph(
                    text="Maps, ride flow, and the NYC pickup dataset. Sign in to open dashboards.",
                    class_name=BODY,
                ),
                _link_label("Sign in", "/login?next=/"),
                build_footer(),
            ],
        )
    ]


def build_api_home(user: UserPublic) -> list[AnyComponent]:
    cards: list[AnyComponent] = [
        c.Link(
            class_name=CARD,
            on_click=GoToEvent(url="/analytics"),
            components=[
                c.Heading(text="NYC pickup analytics", level=3, class_name=_CARD_TITLE),
                c.Paragraph(
                    text="Charts and breakdowns from the FiveThirtyEight Uber pickup feed.",
                    class_name=_CARD_BLURB,
                ),
                c.Paragraph(text="Open →", class_name=_CARD_CTA),
            ],
        ),
    ]
    if user.role == UserRole.rider:
        cards[1:1] = [
            c.Link(
                class_name=CARD,
                on_click=GoToEvent(url="/"),
                components=[
                    c.Heading(text="Rider hub", level=3, class_name=_CARD_TITLE),
                    c.Paragraph(
                        text="Trips, bids on the map, API ride creation, and shortcuts.",
                        class_name=_CARD_BLURB,
                    ),
                    c.Paragraph(text="Open →", class_name=_CARD_CTA),
                ],
            ),
        ]
    elif user.role == UserRole.driver:
        cards.insert(
            1,
            c.Link(
                class_name=CARD,
                on_click=GoToEvent(url="/driver"),
                components=[
                    c.Heading(text="Driver map", level=3, class_name=_CARD_TITLE),
                    c.Paragraph(
                        text="Location, bids on open pickups, trip lifecycle.",
                        class_name=_CARD_BLURB,
                    ),
                    c.Paragraph(text="Open →", class_name=_CARD_CTA),
                ],
            ),
        )
    elif user.role == UserRole.admin:
        cards[1:1] = [
            c.Link(
                class_name=CARD,
                on_click=GoToEvent(url="/admin/dashboard"),
                components=[
                    c.Heading(text="Admin console", level=3, class_name=_CARD_TITLE),
                    c.Paragraph(
                        text="KPIs, fleet map, revenue, and NYC analytics.",
                        class_name=_CARD_BLURB,
                    ),
                    c.Paragraph(text="Open →", class_name=_CARD_CTA),
                ],
            ),
        ]

    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Dashboard — Fruger"),
                build_navbar(user),
                c.Div(
                    class_name=HERO,
                    components=[
                        c.Paragraph(
                            text="Fruger",
                            class_name="text-xs font-semibold uppercase tracking-widest text-white/60",
                        ),
                        c.Heading(
                            text="Welcome back",
                            level=1,
                            class_name="font-display text-3xl font-extrabold tracking-tight mt-2",
                        ),
                        c.Paragraph(
                            text="Maps, ride flow, and the NYC pickup dataset—structured as a single surface.",
                            class_name="text-white/85 mt-3 max-w-xl",
                        ),
                    ],
                ),
                c.Div(
                    class_name=(
                        "grid w-full max-w-6xl grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
                    ),
                    components=cards,
                ),
                build_footer(),
            ],
        )
    ]


def _analytics_table(title: str, rows: list, max_rows: int = 16) -> list[AnyComponent]:
    slice_ = rows[:max_rows]
    if not slice_:
        return [
            c.Heading(text=title, level=2, class_name=TABLE_SECTION_TITLE),
            c.Paragraph(
                text="No rows.",
                class_name="text-fruger-muted mb-8 pl-1",
            ),
        ]
    return [
        c.Heading(text=title, level=2, class_name=TABLE_SECTION_TITLE),
        c.Div(
            class_name=TABLE_WRAP + " mb-10",
            components=[
                c.Table(
                    data=slice_,
                    columns=[
                        DisplayLookup(field="label", title="Category"),
                        DisplayLookup(field="count", title="Pickups"),
                    ],
                    class_name=DATA_TABLE,
                ),
            ],
        ),
    ]


def _nyc_pickup_dataset_body(overview: NycOverviewResponse) -> list[AnyComponent]:
    """Pickups overview: KPI tiles, chart images, and breakdown tables (no page chrome)."""
    t = overview.totals
    parts: list[AnyComponent] = [
        c.Paragraph(
            text=(
                "Historical TLC-style pickups from FiveThirtyEight (seed baseline), "
                "plus new pickup points whenever riders request rides in Fruger. "
                "Neither source includes full trips: no fare, distance, or drop-offs in the CSV feeds."
            ),
            class_name=f"{BODY} max-w-2xl",
        ),
        c.Div(
            class_name="grid grid-cols-2 gap-3 sm:grid-cols-4 my-4",
            components=[
                c.Div(
                    class_name=STAT_TILE,
                    components=[
                        c.Paragraph(
                            text=str(t.total_pickups),
                            class_name="text-2xl font-extrabold text-fruger-on",
                        ),
                        c.Paragraph(
                            text="Total pickups",
                            class_name="text-xs font-semibold uppercase text-fruger-muted",
                        ),
                    ],
                ),
                c.Div(
                    class_name=STAT_TILE,
                    components=[
                        c.Paragraph(
                            text=str(t.pickups_with_latlon),
                            class_name="text-2xl font-extrabold text-fruger-on",
                        ),
                        c.Paragraph(
                            text="With lat/lon",
                            class_name="text-xs font-semibold uppercase text-fruger-muted",
                        ),
                    ],
                ),
                c.Div(
                    class_name=STAT_TILE,
                    components=[
                        c.Paragraph(
                            text=str(t.pickups_with_zone),
                            class_name="text-2xl font-extrabold text-fruger-on",
                        ),
                        c.Paragraph(
                            text="With TLC zone",
                            class_name="text-xs font-semibold uppercase text-fruger-muted",
                        ),
                    ],
                ),
                c.Div(
                    class_name=STAT_TILE,
                    components=[
                        c.Paragraph(
                            text=str(t.distinct_bases),
                            class_name="text-2xl font-extrabold text-fruger-on",
                        ),
                        c.Paragraph(
                            text="Distinct bases",
                            class_name="text-xs font-semibold uppercase text-fruger-muted",
                        ),
                    ],
                ),
            ],
        ),
        c.Heading(text="Charts", level=2, class_name=H2),
        c.Paragraph(
            text="PNG exports rendered with the Fruger palette — open any card in a new tab via the links below.",
            class_name=f"{BODY} max-w-2xl mb-2",
        ),
        build_chart_gallery(
            [
                (
                    "/api/v1/analytics/plots/borough.png",
                    "Pickups by NYC borough",
                    "Borough distribution",
                ),
                (
                    "/api/v1/analytics/plots/base.png",
                    "Pickups by TLC base code",
                    "Dispatching base codes",
                ),
                (
                    "/api/v1/analytics/plots/hour.png",
                    "Pickups by hour of day",
                    "Demand through the day",
                ),
                (
                    "/api/v1/analytics/plots/pickups-by-date.png",
                    "Pickups by date",
                    "Timeline (sample of dates)",
                ),
            ]
        ),
        c.Heading(text="Breakdowns", level=2, class_name=BREAKDOWN_HEADING),
    ]
    parts.extend(_analytics_table("By borough", overview.by_borough))
    parts.extend(_analytics_table("By TLC base", overview.by_base))
    parts.extend(_analytics_table("By hour", overview.by_hour))
    parts.extend(_analytics_table("Top TLC zones", overview.top_zones))
    parts.extend(_analytics_table("By data source era", overview.by_data_source))
    parts.extend(_analytics_table("Pickups by date (sample)", overview.pickups_by_date))
    return parts


def _nyc_analytics_reference_links(
    request_base: str | None = None,
) -> list[AnyComponent]:
    """PNG / raw JSON must use absolute URLs + new tab so the client does not SPA-fetch them."""
    return [
        c.Div(
            class_name="flex flex-wrap gap-3 items-center mt-6",
            components=[
                _outline_link(
                    "NYC overview (JSON API)",
                    "/api/v1/analytics/overview",
                    request_base=request_base,
                    new_tab=True,
                ),
                _outline_link(
                    "This view as FastUI JSON",
                    "/api/nyc",
                    request_base=request_base,
                    new_tab=True,
                ),
            ],
        ),
        c.Paragraph(
            text="Charts as PNG files:",
            class_name="text-xs font-semibold text-fruger-muted mt-4",
        ),
        c.Div(
            class_name="flex flex-wrap gap-3 items-center",
            components=[
                _outline_link(
                    "Borough",
                    "/api/v1/analytics/plots/borough.png",
                    request_base=request_base,
                    new_tab=True,
                ),
                _outline_link(
                    "Base",
                    "/api/v1/analytics/plots/base.png",
                    request_base=request_base,
                    new_tab=True,
                ),
                _outline_link(
                    "Hour",
                    "/api/v1/analytics/plots/hour.png",
                    request_base=request_base,
                    new_tab=True,
                ),
                _outline_link(
                    "Pickups by date",
                    "/api/v1/analytics/plots/pickups-by-date.png",
                    request_base=request_base,
                    new_tab=True,
                ),
            ],
        ),
        c.Paragraph(
            text="Links open in a new tab (full GET) so chart images and JSON are not loaded as FastUI routes.",
            class_name="text-xs text-fruger-muted mt-2",
        ),
    ]


def build_nyc_analytics_embedded_sections(
    overview: NycOverviewResponse | None,
    analytics_error: str | None,
    *,
    request_base: str | None = None,
) -> list[AnyComponent]:
    """NYC pickups content for embedding (e.g. admin console); no navbar or page title."""
    parts: list[AnyComponent] = [
        c.Heading(text="NYC pickup analytics", level=2, class_name=H2),
    ]
    if analytics_error:
        parts.append(c.Paragraph(text=analytics_error, class_name=WARN_SOFT))
        return parts
    if overview is None:
        parts.append(c.Paragraph(text="No overview data.", class_name=BODY))
        return parts
    parts.append(
        c.Div(
            class_name="flex flex-wrap items-center gap-3",
            components=[
                _link_label("Open full-screen analytics", "/analytics"),
            ],
        ),
    )
    parts.extend(_nyc_pickup_dataset_body(overview))
    parts.extend(_nyc_analytics_reference_links(request_base))
    return parts


def build_api_analytics(
    overview: NycOverviewResponse | None,
    analytics_error: str | None,
    user: UserPublic | None = None,
    *,
    request_base: str | None = None,
) -> list[AnyComponent]:
    if analytics_error:
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.PageTitle(text="NYC analytics — Fruger"),
                    build_navbar(user),
                    c.Heading(text="NYC Uber pickups", level=1, class_name=H1),
                    c.Paragraph(text=analytics_error, class_name=WARN_SOFT),
                    build_footer(),
                ],
            )
        ]
    if overview is None:
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.PageTitle(text="NYC analytics — Fruger"),
                    build_navbar(user),
                    c.Heading(text="NYC Uber pickups", level=1, class_name=H1),
                    c.Paragraph(text="No overview data.", class_name=BODY),
                    build_footer(),
                ],
            )
        ]

    parts: list[AnyComponent] = [
        c.PageTitle(text="NYC analytics — Fruger"),
        build_navbar(user),
        c.Heading(text="NYC Uber pickups", level=1, class_name=H1),
        *_nyc_pickup_dataset_body(overview),
        *_nyc_analytics_reference_links(request_base),
        build_footer(),
    ]
    return [c.Page(class_name=PAGE, components=parts)]


def build_driver_fastui(
    request_base: str, user: UserPublic | None = None
) -> list[AnyComponent]:
    src = urljoin(request_base, "/embed/driver")
    return [
        c.Page(
            class_name=PAGE_DRIVER,
            components=[
                c.PageTitle(text="Driver — Fruger"),
                c.Div(class_name="w-full shrink-0", components=[build_navbar(user)]),
                c.Div(
                    class_name="flex-1 min-h-0 min-w-0 w-full",
                    components=[
                        c.Iframe(
                            src=src,
                            title="Driver hub",
                            class_name=IFRAME_DRIVER,
                        ),
                    ],
                ),
            ],
        )
    ]
