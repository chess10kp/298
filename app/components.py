from __future__ import annotations

from typing import Iterable, Tuple

from fastui import components as c
from fastui.events import GoToEvent


def build_footer() -> c.Div:
    """Small product footer with legal and support links."""
    return c.Div(
        class_name="w-full border-t border-fruger-surfaceLow mt-8 pt-6 text-sm text-fruger-muted",
        components=[
            c.Div(
                class_name="max-w-6xl mx-auto px-4 flex items-center justify-between",
                components=[
                    c.Text(text="© 2026 Fruger Inc."),
                ],
            )
        ],
    )


def build_navbar(user: object | None = None) -> c.Div:
    """Very small navbar used across FastUI pages."""
    user_links = []
    if user:
        # display a simple set of links for authenticated users
        user_links = [
            c.Link(components=[c.Text(text="Dashboard")], on_click=GoToEvent(url="/")),
            c.Link(
                components=[c.Text(text="Sign out")],
                on_click=GoToEvent(url="/auth/logout"),
            ),
        ]
    else:
        user_links = [
            c.Link(
                components=[c.Text(text="Sign in")], on_click=GoToEvent(url="/login")
            )
        ]

    return c.Div(
        class_name="w-full max-w-6xl mx-auto px-4 py-4 flex items-center justify-between",
        components=[
            c.Link(components=[c.Text(text="Fruger")], on_click=GoToEvent(url="/")),
            c.Div(class_name="flex items-center gap-4", components=user_links),
        ],
    )


def build_chart_gallery(items: Iterable[Tuple[str, str, str]]) -> c.Div:
    """Render a lightweight grid of chart thumbnails.

    items: iterable of (url, title, subtitle)
    """
    cards = []
    for url, title, subtitle in items:
        cards.append(
            c.Link(
                on_click=GoToEvent(url=url, target="_blank"),
                class_name="w-60 h-36 p-2 bg-fruger-panel rounded shadow-sm",
                components=[
                    c.Heading(text=title, level=4),
                    c.Paragraph(
                        text=subtitle, class_name="text-xs text-fruger-muted mt-1"
                    ),
                ],
            )
        )
    return c.Div(
        class_name="grid grid-cols-1 sm:grid-cols-3 gap-4 my-4", components=cards
    )
