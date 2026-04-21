"""FastUI components for riders."""

from __future__ import annotations

from urllib.parse import urljoin

from fastui import AnyComponent
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from app.components import build_footer, build_navbar
from app.fruger_tailwind import (
    BODY,
    DATA_TABLE,
    EMPTY_STATE,
    H1,
    HERO,
    IFRAME_RIDER,
    LINK,
    PAGE,
    RIDER_MAIN,
    RIDER_PANEL,
    RIDER_PANEL_DESC,
    RIDER_IFRAME_WRAP,
    RIDER_PANEL_HEAD,
    RIDER_PANEL_TITLE,
    RIDER_SECTION_TITLE,
    TABLE_WRAP,
)
from app.schemas.operational import RideOut, UserPublic, UserRole


def _nav_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=LINK,
    )


def _rider_embed_panel(
    title: str,
    description: str,
    *,
    src: str,
    iframe_title: str,
    height: int,
    iframe_class: str,
) -> AnyComponent:
    return c.Div(
        class_name=RIDER_PANEL,
        components=[
            c.Div(
                class_name=RIDER_PANEL_HEAD,
                components=[
                    c.Heading(text=title, level=3, class_name=RIDER_PANEL_TITLE),
                    c.Paragraph(text=description, class_name=RIDER_PANEL_DESC),
                ],
            ),
            c.Div(
                class_name=RIDER_IFRAME_WRAP,
                components=[
                    c.Iframe(
                        src=src,
                        title=iframe_title,
                        height=height,
                        class_name=iframe_class,
                    ),
                ],
            ),
        ],
    )


def build_rider_dashboard(
    user: UserPublic | None,
    rides: list[RideOut],
    *,
    request_base: str | None = None,
) -> list[AnyComponent]:
    if user is None:
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.PageTitle(text="Fruger"),
                    build_navbar(user),
                    c.Heading(text="Fruger", level=1, class_name=H1),
                    c.Paragraph(
                        text="Sign in to request rides and manage trips.",
                        class_name=BODY,
                    ),
                    _nav_link("Go to login", "/login?next=/"),
                    c.Div(
                        class_name="flex flex-wrap items-center gap-1 text-fruger-muted text-sm",
                        components=[
                            c.Text(text="Drivers use the driver map:"),
                            _nav_link("Driver map", "/driver"),
                            c.Text(text="."),
                        ],
                    ),
                ],
            )
        ]
    if user.role != UserRole.rider:
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.PageTitle(text="Rider hub — Fruger"),
                    build_navbar(user),
                    c.Heading(text="Fruger", level=1, class_name=H1),
                    c.Paragraph(
                        text=f"Signed in as {user.email} ({user.role.value}). "
                        "Use a rider account or open the dashboard for your role.",
                        class_name=BODY,
                    ),
                    _nav_link("Admin dashboard", "/admin/dashboard"),
                ],
            )
        ]

    base = request_base or "/"
    bids_src = urljoin(base, "/embed/rider/bids")
    actions_src = urljoin(base, "/embed/rider/actions")

    ride_rows = rides[:50]
    rides_block: list[AnyComponent]
    if ride_rows:
        rides_block = [
            c.Heading(text="Your rides", level=2, class_name=RIDER_SECTION_TITLE),
            c.Div(
                class_name=TABLE_WRAP,
                components=[
                    c.Table(
                        data=list(ride_rows),
                        data_model=RideOut,
                        columns=[
                            DisplayLookup(field="id", title="Ride"),
                            DisplayLookup(field="status", title="Status"),
                            DisplayLookup(field="final_fare_cents", title="Fare (¢)"),
                            DisplayLookup(field="created_at", title="Requested"),
                        ],
                        class_name=DATA_TABLE,
                    ),
                ],
            ),
        ]
    else:
        rides_block = [
            c.Heading(text="Your rides", level=2, class_name=RIDER_SECTION_TITLE),
            c.Paragraph(
                text="No rides yet. Request one using the form below.",
                class_name=EMPTY_STATE,
            ),
        ]

    return [
        c.Page(
            class_name=PAGE,
            components=[
                c.PageTitle(text="Rider hub — Fruger"),
                build_navbar(user),
                c.Div(
                    class_name=HERO,
                    components=[
                        c.Paragraph(
                            text="Rider hub",
                            class_name="text-xs font-semibold uppercase tracking-widest text-white/60",
                        ),
                        c.Heading(
                            text="Welcome back",
                            level=1,
                            class_name="font-display text-2xl sm:text-3xl font-extrabold tracking-tight mt-2",
                        ),
                        c.Paragraph(
                            text=user.email,
                            class_name="text-sm text-white/70 mt-2",
                        ),
                        c.Paragraph(
                            text="Your trips are listed first. Request a ride or review bids in the sections below.",
                            class_name="text-white/85 mt-3 text-sm sm:text-base leading-relaxed",
                        ),
                    ],
                ),
                c.Div(
                    class_name=RIDER_MAIN,
                    components=[
                        *rides_block,
                        c.Heading(
                            text="What you can do",
                            level=2,
                            class_name=RIDER_SECTION_TITLE,
                        ),
                        c.Div(
                            class_name=(
                                "grid grid-cols-1 gap-6"
                            ),
                            components=[
                                _rider_embed_panel(
                                    "Bids on your rides",
                                    "Open rides only. Accepting a bid assigns the driver and closes the rest.",
                                    src=bids_src,
                                    iframe_title="Rider bids",
                                    height=600,
                                    iframe_class=f"{IFRAME_RIDER} min-h-[360px] lg:min-h-[520px]",
                                ),
                                _rider_embed_panel(
                                    "Request or cancel",
                                    "Search pickup and drop-off, place a request, or cancel by ride ID.",
                                    src=actions_src,
                                    iframe_title="Rider ride actions",
                                    height=480,
                                    iframe_class=f"{IFRAME_RIDER} min-h-[320px] lg:min-h-[440px]",
                                ),
                            ],
                        ),
                    ],
                ),
                build_footer(),
            ],
        )
    ]
