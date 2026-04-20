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
    CARD,
    EMPTY_STATE,
    H1,
    H2,
    HERO,
    IFRAME,
    IFRAME_ACTIONS,
    LINK,
    PAGE,
    TABLE_WRAP,
)
from app.schemas.operational import RideOut, UserPublic, UserRole

_CARD_TITLE = "font-display text-lg font-bold text-fruger-on"
_CARD_BLURB = "text-sm text-fruger-muted mt-1"
_CARD_CTA = "text-xs font-bold uppercase tracking-wide text-fruger-accent mt-3"


def _nav_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=LINK,
    )


def _quick_card(title: str, description: str, url: str) -> AnyComponent:
    return c.Link(
        class_name=CARD,
        on_click=GoToEvent(url=url),
        components=[
            c.Heading(text=title, level=3, class_name=_CARD_TITLE),
            c.Paragraph(text=description, class_name=_CARD_BLURB),
            c.Paragraph(text="Open →", class_name=_CARD_CTA),
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
                        class_name="flex flex-wrap items-center gap-1 text-fruger-muted",
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
                        text=f"Logged in as {user.email} ({user.role.value}). "
                        "Register a rider account or open the correct dashboard.",
                        class_name=BODY,
                    ),
                    _nav_link("Admin dashboard", "/admin/dashboard"),
                ],
            )
        ]

    ride_rows = rides[:50]
    table: list[AnyComponent] = []
    if ride_rows:
        table = [
            c.Heading(text="Your rides", level=2, class_name=H2),
            c.Div(
                class_name=TABLE_WRAP,
                components=[
                    c.Table(
                        data=list(ride_rows),
                        data_model=RideOut,
                        columns=[
                            DisplayLookup(field="id"),
                            DisplayLookup(field="status"),
                            DisplayLookup(field="final_fare_cents"),
                            DisplayLookup(field="created_at"),
                        ],
                        class_name="w-full text-sm",
                    ),
                ],
            ),
        ]
    else:
        table = [
            c.Heading(text="Your rides", level=2, class_name=H2),
            c.Paragraph(
                text="No rides yet. Use the request form to create one.",
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
                            class_name="font-display text-3xl font-extrabold tracking-tight mt-2",
                        ),
                        c.Paragraph(
                            text=(
                                f"Signed in as {user.email}. Request rides below, "
                                "review bids, and track trips in one place."
                            ),
                            class_name="text-white/85 mt-3 max-w-xl",
                        ),
                    ],
                ),
                c.Heading(text="Quick access", level=2, class_name=H2),
                c.Div(
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 items-start w-full",
                    components=[
                        c.Div(
                            class_name="space-y-2 min-w-0",
                            components=[
                                c.Paragraph(
                                    text="Bids",
                                    class_name="text-xs font-semibold uppercase tracking-widest text-fruger-muted",
                                ),
                                c.Heading(
                                    text="Bids on your rides", level=2, class_name=H2
                                ),
                                c.Paragraph(
                                    text=(
                                        "Open rides only. Accepting assigns the driver and closes competing bids."
                                    ),
                                    class_name=BODY,
                                ),
                                c.Iframe(
                                    src=urljoin(
                                        request_base or "/", "/embed/rider/bids"
                                    ),
                                    title="Rider bids",
                                    height=640,
                                    class_name=IFRAME,
                                ),
                            ],
                        ),
                        c.Div(
                            class_name="space-y-2 min-w-0",
                            components=[
                                c.Paragraph(
                                    text="Request & manage rides",
                                    class_name="text-xs font-semibold uppercase tracking-widest text-fruger-muted",
                                ),
                                c.Heading(
                                    text="New ride & cancellation",
                                    level=2,
                                    class_name=H2,
                                ),
                                c.Paragraph(
                                    text="Use the embedded form: search pickup and drop-off, request a ride, or cancel by ID.",
                                    class_name="text-sm text-fruger-muted",
                                ),
                                c.Iframe(
                                    src=urljoin(
                                        request_base or "/", "/embed/rider/actions"
                                    ),
                                    title="Rider ride actions",
                                    height=520,
                                    class_name=IFRAME_ACTIONS,
                                ),
                            ],
                        ),
                    ],
                ),
                *table,
                build_footer(),
            ],
        )
    ]
