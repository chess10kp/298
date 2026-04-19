"""Shared FastUI components: navbar and footer."""

from __future__ import annotations

from fastui import AnyComponent, components as c
from fastui.events import GoToEvent

from app.fruger_tailwind import FOOTER, NAVBAR
from app.schemas.operational import UserPublic


def build_navbar(user: UserPublic | None) -> c.Navbar:
    end_links: list[AnyComponent] = []
    if user is not None:
        end_links.append(
            c.Link(
                components=[c.Text(text="Logout")],
                on_click=GoToEvent(url="/api/auth/logout"),
                class_name="text-sm font-semibold text-white/80 hover:text-white",
            )
        )

    return c.Navbar(
        class_name=NAVBAR,
        title="Fruger",
        title_event=GoToEvent(url="/"),
        end_links=end_links,
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
