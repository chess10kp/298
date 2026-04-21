"""Shared FastUI components: navbar and footer."""

from __future__ import annotations

from fastui import AnyComponent, components as c
from fastui.events import GoToEvent

from app.fruger_tailwind import CHART_CAPTION, CHART_CARD, CHART_GALLERY, FOOTER, IMG, NAVBAR
from app.schemas.operational import UserPublic


def build_navbar(user: UserPublic | None) -> c.Div:
    items: list[AnyComponent] = []
    if user is not None:
        items.append(
            c.Link(
                components=[c.Text(text="Log out")],
                # FastUI requests ``/api`` + path (with or without a trailing slash).
                # See :func:`app.routers.fruger_fastui.api_auth_logout_fastui`.
                on_click=GoToEvent(url="/auth/logout"),
                class_name="text-sm font-semibold text-fruger-accent hover:underline",
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
            c.Div(class_name="flex items-center gap-5 sm:gap-6", components=items),
        ],
    )


def build_chart_gallery(
    charts: list[tuple[str, str, str]],
) -> c.Div:
    """PNG chart grid: each item is ``(image_url, alt, caption)``."""
    cards: list[AnyComponent] = []
    for src, alt, caption in charts:
        cards.append(
            c.Div(
                class_name=CHART_CARD,
                components=[
                    c.Image(
                        src=src,
                        alt=alt,
                        class_name=IMG + " w-full rounded-lg",
                    ),
                    c.Paragraph(text=caption, class_name=CHART_CAPTION),
                ],
            )
        )
    return c.Div(class_name=CHART_GALLERY, components=cards)


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
