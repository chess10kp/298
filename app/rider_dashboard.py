"""FastUI components for riders."""

from __future__ import annotations

from fastui import AnyComponent, components as c
from fastui.components.display import DisplayLookup

from app.schemas.operational import RideOut, UserPublic, UserRole


def build_rider_dashboard(user: UserPublic | None, rides: list[RideOut]) -> list[AnyComponent]:
    if user is None:
        return [
            c.Page(
                components=[
                    c.Heading(text="Rider", level=1),
                    c.Text(text="Sign in to request rides and manage trips."),
                    c.Link(
                        href="/login?next=/api/rider/dashboard",
                        text="Go to login",
                    ),
                    c.Text(text="Drivers use the driver map: "),
                    c.Link(href="/driver", text="/driver"),
                    c.Text(text="."),
                ]
            )
        ]
    if user.role != UserRole.rider:
        return [
            c.Page(
                components=[
                    c.Heading(text="Rider area", level=1),
                    c.Text(
                        text=f"Logged in as {user.email} ({user.role.value}). "
                        "Register a rider account or open the correct dashboard."
                    ),
                    c.Link(href="/api/admin/dashboard", text="Admin dashboard"),
                ]
            )
        ]

    ride_rows = rides[:50]
    table: list[AnyComponent] = []
    if ride_rows:
        table = [
            c.Heading(text="Your rides", level=2),
            c.Table(
                data=[r.model_dump(mode="json") for r in ride_rows],
                columns=[
                    DisplayLookup(field="id"),
                    DisplayLookup(field="status"),
                    DisplayLookup(field="final_fare_cents"),
                    DisplayLookup(field="created_at"),
                ],
            ),
        ]
    else:
        table = [c.Text(text="No rides yet.")]

    return [
        c.Page(
            components=[
                c.Heading(text=f"Hello, {user.email}", level=1),
                c.Link(href="/", text="App dashboard"),
                c.Text(text=" "),
                c.Text(
                    text="Create rides via POST /api/rides (see API docs). "
                    "Cancel with POST /api/rides/{id}/cancel. Log out with POST /api/auth/logout."
                ),
                c.Heading(text="Quick links", level=2),
                c.Link(href="/rider/bids", text="View and accept bids"),
                c.Text(text=" "),
                c.Link(href="/api/docs", text="API docs"),
                *table,
            ]
        )
    ]
