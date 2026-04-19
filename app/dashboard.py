"""FastUI dashboard for NYC TLC Uber pickup analytics."""

from fastui import AnyComponent, components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from app.analytics_queries import fetch_overview
from app.config import DB_PATH
from app.fruger_tailwind import (
    BODY,
    H1,
    H2,
    IMG,
    OUTLINE_BTN,
    PAGE,
    TABLE_WRAP,
    WARN_SOFT,
)
from app.schemas.analytics import CountByLabel


def _open_endpoint_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=OUTLINE_BTN,
    )


def build_dashboard() -> list[AnyComponent]:
    if not DB_PATH.is_file():
        return [
            c.Page(
                class_name=PAGE,
                components=[
                    c.Heading(text="Fruger · NYC pickup analytics", level=1, class_name=H1),
                    c.Paragraph(
                        text="Database not found. Start the app once (Kaggle auth or place "
                        "uber-raw-data-apr14.csv under data/) to create fruger.db.",
                        class_name=WARN_SOFT,
                    ),
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

    def _table(title: str, rows: list[CountByLabel], max_rows: int = 12) -> list[AnyComponent]:
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

    components: list[AnyComponent] = [
        c.Heading(text="Fruger · NYC Uber pickup analytics", level=1, class_name=H1),
        c.Paragraph(
            text="Source: FiveThirtyEight — Uber pickups in New York City "
            "(TLC pickup events; not full trips — no fare, distance, or drop-offs).",
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
        c.Image(src="/api/analytics/plots/borough.png", alt="By borough", class_name=IMG),
        c.Image(src="/api/analytics/plots/base.png", alt="By TLC base", class_name=IMG),
        c.Image(src="/api/analytics/plots/hour.png", alt="By hour", class_name=IMG),
        c.Image(
            src="/api/analytics/plots/pickups-by-date.png",
            alt="By date",
            class_name=IMG,
        ),
    ]

    components.extend(_table("Pickups by borough", overview.by_borough))
    components.extend(_table("Pickups by TLC base", overview.by_base))
    components.extend(_table("Pickups by hour", overview.by_hour))
    components.extend(_table("Top TLC zones", overview.top_zones))
    components.extend(_table("By data file era (2014 vs 2015)", overview.by_data_source))
    components.extend(_table("Pickups by date (sample)", overview.pickups_by_date))

    components.extend(
        [
            c.Div(
                class_name="flex flex-wrap gap-3 items-center mt-6",
                components=[
                    _open_endpoint_link("NYC overview (JSON API)", "/api/analytics/overview"),
                    _open_endpoint_link("This page as FastUI JSON", "/api/nyc"),
                ],
            ),
            c.Paragraph(
                text="Use the buttons to fetch the same data in JSON form.",
                class_name="text-xs text-fruger-muted mt-2",
            ),
        ]
    )
    return [c.Page(class_name=PAGE, components=components)]
