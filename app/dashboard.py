"""FastUI dashboard for NYC TLC Uber pickup analytics."""

from fastui import AnyComponent
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from app.analytics_queries import fetch_overview
from app.components import build_chart_gallery, build_footer, build_navbar
from app.config import DB_PATH
from app.fruger_tailwind import (
    BODY,
    BREAKDOWN_HEADING,
    DATA_TABLE,
    H1,
    H2,
    OUTLINE_BTN,
    PAGE,
    TABLE_SECTION_TITLE,
    TABLE_WRAP,
    WARN_SOFT,
)
from app.schemas.analytics import CountByLabel
from app.schemas.operational import UserPublic


def _open_endpoint_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=OUTLINE_BTN,
    )


def build_dashboard(user: UserPublic | None = None) -> list[AnyComponent]:
    if not DB_PATH.is_file():
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.Heading(
                        text="Fruger · NYC pickup analytics", level=1, class_name=H1
                    ),
                    build_navbar(user),
                    c.Paragraph(
                        text="Database not found. Start the app once (Kaggle auth or place "
                        "uber-raw-data-apr14.csv under data/) to create fruger.db.",
                        class_name=WARN_SOFT,
                    ),
                    build_footer(),
                ],
            )
        ]

    overview = fetch_overview(DB_PATH)
    t = overview.totals

    summary_lines = [
        f"Total pickups: {t.total_pickups}",
        f"With latitude/longitude (2014): {t.pickups_with_latlon}",
        f"With TLC zone label (2015 + lookup): {t.pickups_with_zone}",
        f"Distinct TLC bases: {t.distinct_bases}",
    ]

    def _table(
        title: str, rows: list[CountByLabel], max_rows: int = 12
    ) -> list[AnyComponent]:
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

    components: list[AnyComponent] = [
        c.Heading(text="Fruger · NYC Uber pickup analytics", level=1, class_name=H1),
        build_navbar(user),
        c.Paragraph(
            text=(
                "One pickups table in SQLite: TLC/Kaggle seed rows plus a new row for each "
                "Fruger ride request, so demand analytics and map labels share the same stream. "
                "Those CSVs are pickup-only (no fare); trip prices live on marketplace rides."
            ),
            class_name=BODY,
        ),
        c.Div(
            class_name="rounded-md bg-fruger-panel p-4 shadow-fruger-float space-y-1",
            components=[
                c.Paragraph(text=line, class_name="font-mono text-sm text-fruger-on")
                for line in summary_lines
            ],
        ),
        c.Heading(text="Charts", level=2, class_name=H2),
        build_chart_gallery(
            [
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
    ]

    components.append(
        c.Heading(text="Breakdowns", level=2, class_name=BREAKDOWN_HEADING),
    )
    components.extend(
        _table("Pickup stream (seed vs live, same table)", overview.by_pickup_source)
    )
    components.extend(_table("Pickups by TLC base", overview.by_base))
    components.extend(_table("Pickups by hour", overview.by_hour))
    components.extend(_table("Top TLC zones", overview.top_zones))
    components.extend(
        _table("By data file era (2014 vs 2015)", overview.by_data_source)
    )
    components.extend(_table("Pickups by date (sample)", overview.pickups_by_date))

    components.extend(
        [
            c.Div(
                class_name="flex flex-wrap gap-3 items-center mt-6",
                components=[
                    _open_endpoint_link(
                        "NYC overview (JSON API)", "/api/analytics/overview"
                    ),
                    _open_endpoint_link("This page as FastUI JSON", "/api/nyc"),
                ],
            ),
            c.Paragraph(
                text="Use the buttons to fetch the same data in JSON form.",
                class_name="text-xs text-fruger-muted mt-2",
            ),
            build_footer(),
        ]
    )
    return [c.Page(class_name=PAGE, components=components)]
