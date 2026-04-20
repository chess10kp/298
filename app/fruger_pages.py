"""FastUI page trees for Fruger (replaces Jinja templates)."""

from __future__ import annotations

from urllib.parse import urljoin

from fastui import AnyComponent
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from app.components import build_footer, build_navbar
from app.fruger_tailwind import (
    BODY,
    CARD,
    H1,
    H2,
    HERO,
    IFRAME,
    IFRAME_TALL,
    IMG,
    LINK,
    OUTLINE_BTN,
    PAGE,
    STAT_TILE,
    TABLE_WRAP,
    WARN_SOFT,
)
from app.schemas.analytics import NycOverviewResponse
from app.schemas.operational import UserPublic, UserRole

_CARD_TITLE = "font-display text-lg font-bold text-fruger-on"
_CARD_BLURB = "text-sm text-fruger-muted mt-1"
_CARD_CTA = "text-xs font-bold uppercase tracking-wide text-fruger-accent mt-3"


def _link_label(text: str, url: str, class_name: str | None = None) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=class_name or LINK,
    )


def _outline_link(text: str, url: str) -> AnyComponent:
    """Button-styled link for opening JSON or static assets (GET)."""
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
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
                        text="Volume, revenue, operational links.",
                        class_name=_CARD_BLURB,
                    ),
                    c.Paragraph(text="Open →", class_name=_CARD_CTA),
                ],
            ),
            c.Link(
                class_name=CARD,
                on_click=GoToEvent(url="/admin/map"),
                components=[
                    c.Heading(text="Fleet map", level=3, class_name=_CARD_TITLE),
                    c.Paragraph(
                        text="Last reported driver GPS positions.",
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
                build_footer(),
            ],
        )
    ]


def _analytics_table(title: str, rows: list, max_rows: int = 16) -> list[AnyComponent]:
    slice_ = rows[:max_rows]
    if not slice_:
        return [
            c.Heading(text=title, level=2, class_name=H2),
            c.Paragraph(text="No rows.", class_name="text-fruger-muted"),
        ]
    return [
        c.Heading(text=title, level=2, class_name=H2),
        c.Div(
            class_name=TABLE_WRAP,
            components=[
                c.Table(
                    data=slice_,
                    columns=[
                        DisplayLookup(field="label"),
                        DisplayLookup(field="count"),
                    ],
                    class_name="w-full text-sm",
                ),
            ],
        ),
    ]


def build_api_analytics(
    overview: NycOverviewResponse | None,
    analytics_error: str | None,
    user: UserPublic | None = None,
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

    t = overview.totals
    parts: list[AnyComponent] = [
        c.PageTitle(text="NYC analytics — Fruger"),
        build_navbar(user),
        c.Heading(text="NYC Uber pickups", level=1, class_name=H1),
        c.Paragraph(
            text="TLC-style events from FiveThirtyEight—not full trips: no fare, distance, or drop-offs in the source files.",
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
        c.Image(
            src="/api/v1/analytics/plots/borough.png", alt="By borough", class_name=IMG
        ),
        c.Image(src="/api/v1/analytics/plots/base.png", alt="By base", class_name=IMG),
        c.Image(src="/api/v1/analytics/plots/hour.png", alt="By hour", class_name=IMG),
        c.Image(
            src="/api/v1/analytics/plots/pickups-by-date.png",
            alt="By date",
            class_name=IMG,
        ),
        c.Heading(text="Breakdowns", level=2, class_name=H2),
    ]
    parts.extend(_analytics_table("By borough", overview.by_borough))
    parts.extend(_analytics_table("By TLC base", overview.by_base))
    parts.extend(_analytics_table("By hour", overview.by_hour))
    parts.extend(_analytics_table("Top TLC zones", overview.top_zones))
    parts.extend(_analytics_table("By data source era", overview.by_data_source))
    parts.extend(_analytics_table("Pickups by date (sample)", overview.pickups_by_date))
    parts.extend(
        [
            c.Div(
                class_name="flex flex-wrap gap-3 items-center mt-6",
                components=[
                    _outline_link(
                        "NYC overview (JSON API)", "/api/v1/analytics/overview"
                    ),
                    _outline_link("This view as FastUI JSON", "/api/nyc"),
                ],
            ),
            c.Paragraph(
                text="Charts as PNG files:",
                class_name="text-xs font-semibold text-fruger-muted mt-4",
            ),
            c.Div(
                class_name="flex flex-wrap gap-3 items-center",
                components=[
                    _outline_link("Base", "/api/analytics/plots/base.png"),
                    _outline_link("Hour", "/api/analytics/plots/hour.png"),
                    _outline_link(
                        "Pickups by date", "/api/analytics/plots/pickups-by-date.png"
                    ),
                ],
            ),
            c.Paragraph(
                text="Use the JSON link for structured data; PNG links open chart images.",
                class_name="text-xs text-fruger-muted mt-2",
            ),
            build_footer(),
        ]
    )
    return [c.Page(class_name=PAGE, components=parts)]


def build_driver_fastui(
    request_base: str, user: UserPublic | None = None
) -> list[AnyComponent]:
    src = urljoin(request_base, "/embed/driver")
    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Driver — Fruger"),
                build_navbar(user),
                c.Paragraph(
                    text="Partner",
                    class_name="text-xs font-semibold uppercase tracking-widest text-fruger-muted",
                ),
                c.Heading(text="Driver map", level=1, class_name=H1),
                c.Paragraph(
                    text="Session-backed location updates. Open rides appear as numbered pickup markers. "
                    "Select a ride from a marker, then route or bid.",
                    class_name=BODY,
                ),
                c.Iframe(
                    src=src,
                    title="Driver map",
                    height=560,
                    class_name=IFRAME_TALL,
                ),
                build_footer(),
            ],
        )
    ]


def build_admin_map_fastui(
    request_base: str, user: UserPublic | None = None
) -> list[AnyComponent]:
    src = urljoin(request_base, "/embed/admin/map")
    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Fleet map — Fruger"),
                build_navbar(user),
                c.Paragraph(
                    text="Fleet",
                    class_name="text-xs font-semibold uppercase tracking-widest text-fruger-muted",
                ),
                c.Heading(text="Partner map", level=1, class_name=H1),
                c.Paragraph(
                    text="Last reported driver GPS from driver_locations. Polls every 10s.",
                    class_name=BODY,
                ),
                _link_label("Admin console", "/admin/dashboard"),
                c.Iframe(
                    src=src,
                    title="Fleet map",
                    height=560,
                    class_name=IFRAME_TALL,
                ),
                build_footer(),
            ],
        )
    ]


def build_rider_bids_fastui(
    request_base: str, user: UserPublic | None = None
) -> list[AnyComponent]:
    src = urljoin(request_base, "/embed/rider/bids")
    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Bids — Fruger"),
                build_navbar(user),
                c.Paragraph(
                    text="Rider",
                    class_name="text-xs font-semibold uppercase tracking-widest text-fruger-muted",
                ),
                c.Heading(text="Bids on your rides", level=1, class_name=H1),
                c.Paragraph(
                    text="Open rides only. Accepting assigns the driver and closes competing bids.",
                    class_name=BODY,
                ),
                c.Div(
                    class_name="flex flex-wrap gap-3 items-center",
                    components=[
                        _link_label("Rider hub", "/"),
                    ],
                ),
                c.Iframe(
                    src=src,
                    title="Rider bids",
                    height=640,
                    class_name=IFRAME,
                ),
                build_footer(),
            ],
        )
    ]
