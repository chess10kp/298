"""FastUI dashboard for NYC TLC Uber pickup analytics."""

from fastui import AnyComponent, components as c
from fastui.components.display import DisplayLookup

from app.analytics_queries import fetch_overview
from app.config import DB_PATH
from app.schemas.analytics import CountByLabel


def build_dashboard() -> list[AnyComponent]:
    if not DB_PATH.is_file():
        return [
            c.Page(
                components=[
                    c.Heading(text="NYC Uber pickup analytics", level=1),
                    c.Text(
                        text="Database not found. Start the app once (Kaggle auth or place "
                        "uber-raw-data-apr14.csv under data/) to create fruger.db."
                    ),
                ]
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
            return [c.Heading(text=title, level=2), c.Text(text="No rows.")]
        return [
            c.Heading(text=title, level=2),
            c.Table(
                data=slice_,
                columns=[
                    DisplayLookup(field="label"),
                    DisplayLookup(field="count"),
                ],
            ),
        ]

    components: list[AnyComponent] = [
        c.Heading(text="NYC Uber pickup analytics", level=1),
        c.Text(
            text="Source: FiveThirtyEight — Uber pickups in New York City "
            "(TLC pickup events; not full trips — no fare, distance, or drop-offs)."
        ),
        *[c.Text(text=line) for line in summary_lines],
        c.Heading(text="Charts", level=2),
        c.Image(src="/api/analytics/plots/borough.png", alt="By borough", class_name="img-fluid"),
        c.Image(src="/api/analytics/plots/base.png", alt="By TLC base", class_name="img-fluid"),
        c.Image(src="/api/analytics/plots/hour.png", alt="By hour", class_name="img-fluid"),
        c.Image(
            src="/api/analytics/plots/pickups-by-date.png",
            alt="By date",
            class_name="img-fluid",
        ),
    ]

    components.extend(_table("Pickups by borough", overview.by_borough))
    components.extend(_table("Pickups by TLC base", overview.by_base))
    components.extend(_table("Pickups by hour", overview.by_hour))
    components.extend(_table("Top TLC zones", overview.top_zones))
    components.extend(_table("By data file era (2014 vs 2015)", overview.by_data_source))
    components.extend(_table("Pickups by date (sample)", overview.pickups_by_date))

    return [c.Page(components=components)]
