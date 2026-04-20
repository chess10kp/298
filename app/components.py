"""Shared FastUI components: navbar and footer."""

from __future__ import annotations

from fastui import AnyComponent, components as c
from fastui.events import GoToEvent

from app.fruger_tailwind import FOOTER, NAVBAR
from app.schemas.operational import UserPublic


def build_navbar(user: UserPublic | None) -> c.Div:
    right: list[AnyComponent] = []
    if user is not None:
        right.append(
            c.Link(
                components=[c.Text(text="Logout")],
                # Use the FastUI logout path. FastUI client prefixes API calls
                # with /api, so the correct target here is /auth/logout which
                # resolves to /api/v1/auth/logout on the client-side.
                on_click=GoToEvent(url="/auth/logout"),
                class_name="text-sm font-semibold text-fruger-accent hover:underline ml-4",
            )
        )

    return c.Div(
        class_name=NAVBAR,
        components=[
            c.Link(
                components=[c.Text(text="Fruger")],
                on_click=GoToEvent(url="/"),
                class_name="font-display text-base font-bold text-fruger-on no-underline hover:opacity-80",
            ),
            c.Div(
                class_name="flex items-center",
                components=right,
            ),
        ],
    )


def build_footer() -> c.Div:
    return c.Div(
        class_name=FOOTER,
        components=[
            c.Paragraph(
                text="Fruger — Ride marketplace & NYC pickup analytics",
                class_name="text-xs text-fruger-muted",
            ),
        ],
    )
