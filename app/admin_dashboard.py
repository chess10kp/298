"""FastUI components for admins."""

from __future__ import annotations

from urllib.parse import urljoin

from fastui import AnyComponent, components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from pydantic import BaseModel

from app.components import build_footer, build_navbar
from app.fruger_pages import build_nyc_analytics_embedded_sections
from app.fruger_tailwind import (
    BODY,
    CHART_CAPTION,
    CHART_CARD,
    DATA_TABLE,
    EMPTY_STATE,
    H1,
    H2,
    IMG,
    LINK,
    PAGE,
    STAT_TILE,
    TABLE_SECTION_TITLE,
    TABLE_WRAP,
)

# FastUI prebuilt passes only src/width/height/title/sandbox/srcDoc to <iframe> — no className.
_ADMIN_FLEET_SHELL = (
    "admin-fleet-map-shell w-full max-w-none rounded-md shadow-fruger-float overflow-hidden "
    "border border-fruger-container bg-fruger-surface"
)
from app.schemas.analytics import NycOverviewResponse
from app.schemas.admin_metrics import AdminMetricsOut, LabeledCount
from app.schemas.operational import AdminStatsOut, RideStatus, UserPublic

_MUTED = "text-xs font-medium uppercase tracking-wide text-fruger-muted"
_STAT_VALUE = "font-display text-4xl font-extrabold tracking-tight text-fruger-on mt-2"
_STAT_HINT = "text-sm text-fruger-muted mt-2"
_CARD_TITLE = "font-display text-xl font-bold text-fruger-on"
_CARD_BLURB = "text-sm text-fruger-muted mt-1"


class _RidesByStatusRow(BaseModel):
    status: str
    count: int


class _LabelMetricRow(BaseModel):
    label: str
    count: int


def _as_rows(items: list[LabeledCount]) -> list[_LabelMetricRow]:
    return [_LabelMetricRow(label=i.label, count=i.count) for i in items]


def _metric_table(title: str, items: list[LabeledCount], *, max_rows: int = 12) -> list[AnyComponent]:
    rows = _as_rows(items[:max_rows])
    if not rows:
        return [
            c.Heading(text=title, level=2, class_name=TABLE_SECTION_TITLE),
            c.Div(
                class_name=EMPTY_STATE + " mb-6",
                components=[c.Paragraph(text="No rows yet.", class_name=BODY)],
            ),
        ]
    return [
        c.Heading(text=title, level=2, class_name=TABLE_SECTION_TITLE),
        c.Div(
            class_name=TABLE_WRAP + " mb-8",
            components=[
                c.Table(
                    data=rows,
                    data_model=_LabelMetricRow,
                    columns=[
                        DisplayLookup(field="label", title="Category"),
                        DisplayLookup(field="count", title="Count"),
                    ],
                    class_name=DATA_TABLE,
                )
            ],
        ),
    ]


def _nav_link(text: str, url: str) -> AnyComponent:
    return c.Link(
        components=[c.Text(text=text)],
        on_click=GoToEvent(url=url),
        class_name=LINK,
    )


def _status_label(raw: str) -> str:
    return raw.replace("_", " ").title()


def _stat_tile(*, label: str, value: str, hint: str | None = None) -> AnyComponent:
    inner: list[AnyComponent] = [
        c.Paragraph(text=label, class_name=_MUTED),
        c.Paragraph(text=value, class_name=_STAT_VALUE),
    ]
    if hint:
        inner.append(c.Paragraph(text=hint, class_name=_STAT_HINT))
    return c.Div(class_name=STAT_TILE, components=inner)


def build_admin_dashboard(
    stats: AdminStatsOut,
    metrics: AdminMetricsOut,
    user: UserPublic | None = None,
    *,
    nyc_overview: NycOverviewResponse | None = None,
    nyc_error: str | None = None,
    request_base: str | None = None,
) -> list[AnyComponent]:
    rev_dollars = stats.completed_revenue_cents / 100.0
    rev_primary = f"${rev_dollars:,.2f}"
    n = stats.revenue_ride_count
    completed_total = stats.rides_by_status.get(RideStatus.completed.value, 0)
    omitted = max(0, completed_total - n)
    if n == 0:
        rev_hint = (
            "No completed marketplace rides with fares yet. "
            "Pickup rows (seed + live) never carry fares—only rides do."
        )
    else:
        trip_word = "trip" if n == 1 else "trips"
        rev_hint = (
            f"Marketplace fares only (rides table): final amounts on {n:,} completed {trip_word}. "
            "Pickup seed rows track demand/location, not price."
        )
        if omitted:
            oword = "ride" if omitted == 1 else "rides"
            rev_hint += f" {omitted:,} completed {oword} omitted (no final_fare_cents in the database)."

    status_rows = [
        _RidesByStatusRow(status=_status_label(k), count=v)
        for k, v in sorted(stats.rides_by_status.items())
    ]
    status_section: list[AnyComponent] = [
        c.Heading(
            text="Rides by status",
            level=2,
            class_name=TABLE_SECTION_TITLE,
        ),
    ]
    if status_rows:
        status_section.append(
            c.Div(
                class_name=TABLE_WRAP + " mb-8",
                components=[
                    c.Table(
                        data=status_rows,
                        data_model=_RidesByStatusRow,
                        columns=[
                            DisplayLookup(field="status", title="Status"),
                            DisplayLookup(field="count", title="Rides"),
                        ],
                        class_name=DATA_TABLE,
                    ),
                ],
            )
        )
    else:
        status_section.append(
            c.Div(
                class_name=EMPTY_STATE,
                components=[
                    c.Paragraph(text="No rides in the database yet.", class_name=BODY),
                ],
            )
        )

    funnel = metrics.funnel
    bid_market = metrics.bid_market
    revenue_metrics = metrics.revenue_fares
    driver_snapshot = metrics.driver_snapshot
    demand = metrics.demand

    components: list[AnyComponent] = [
        build_navbar(user),
        c.Heading(text="Fruger admin", level=1, class_name=H1),
        c.Div(
            class_name="flex flex-wrap gap-3",
            components=[_nav_link("Fruger home", "/")],
        ),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Marketplace rides",
                    value=f"{stats.total_rides:,}",
                    hint="Trip lifecycle and fares (rides table); each request also appends a pickups row",
                ),
                _stat_tile(
                    label="Pickup stream rows",
                    value=f"{stats.nyc_pickup_records:,}",
                    hint="Single pickups table: TLC/Kaggle seed plus one analytics row per ride request",
                ),
                _stat_tile(
                    label="Total bids",
                    value=f"{stats.total_bids:,}",
                    hint="Driver offers on rides",
                ),
                _stat_tile(
                    label="Fruger ride revenue",
                    value=rev_primary,
                    hint=rev_hint,
                ),
            ],
        ),
        c.Heading(text="Fleet map", level=2, class_name=H2),
        c.Div(
            class_name=CHART_CARD + " w-full max-w-none",
            components=[
                *(
                    [
                        c.Div(
                            class_name=_ADMIN_FLEET_SHELL,
                            components=[
                                c.Iframe(
                                    src=urljoin(request_base + "/", "embed/admin/map"),
                                    title="Fleet map",
                                    width="100%",
                                )
                            ],
                        )
                    ]
                    if request_base
                    else [
                        c.Paragraph(
                            text="Map embed unavailable (missing request base URL).",
                            class_name=BODY,
                        )
                    ]
                ),
            ],
        ),
        c.Heading(text="Marketplace funnel", level=2, class_name=H2),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Assigned+ progressed",
                    value=f"{(funnel.assigned + funnel.in_progress + funnel.completed):,}",
                    hint=f"{funnel.assign_rate * 100:.1f}% of all rides",
                ),
                _stat_tile(
                    label="Completed rides",
                    value=f"{funnel.completed:,}",
                    hint=f"{funnel.completion_rate * 100:.1f}% completion rate",
                ),
                _stat_tile(
                    label="Cancelled rides",
                    value=f"{funnel.cancelled:,}",
                    hint=f"{funnel.cancellation_rate * 100:.1f}% cancellation rate",
                ),
                _stat_tile(
                    label="Still bidding",
                    value=f"{funnel.bidding_open:,}",
                    hint="Open rides awaiting assignment",
                ),
            ],
        ),
        c.Heading(text="Bid market health", level=2, class_name=H2),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Avg bids per ride",
                    value=f"{bid_market.avg_bids_per_ride:.2f}",
                    hint=f"Median {bid_market.median_bids_per_ride:.1f}",
                ),
                _stat_tile(
                    label="Rides with zero bids",
                    value=f"{bid_market.rides_with_zero_bids:,}",
                    hint=f"{bid_market.rides_with_bids:,} rides received bids",
                ),
                _stat_tile(
                    label="Accepted bids",
                    value=f"{bid_market.accepted_bids:,}",
                    hint=f"{bid_market.bid_acceptance_rate * 100:.1f}% acceptance rate",
                ),
                _stat_tile(
                    label="Distinct bidding drivers",
                    value=f"{bid_market.distinct_bidding_drivers:,}",
                    hint="Unique drivers who submitted at least one bid",
                ),
            ],
        ),
        c.Heading(text="Fare and revenue quality", level=2, class_name=H2),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Avg completed fare",
                    value=f"${revenue_metrics.avg_completed_fare_cents / 100.0:,.2f}",
                    hint=f"Median ${revenue_metrics.median_completed_fare_cents / 100.0:,.2f}",
                ),
                _stat_tile(
                    label="Avg accepted bid",
                    value=f"${revenue_metrics.avg_accepted_bid_cents / 100.0:,.2f}",
                    hint=f"Median ${revenue_metrics.median_accepted_bid_cents / 100.0:,.2f}",
                ),
                _stat_tile(
                    label="Final minus accepted",
                    value=f"${revenue_metrics.avg_final_minus_accepted_cents / 100.0:,.2f}",
                    hint=f"{revenue_metrics.paired_completed_with_accepted_bid:,} paired completed rides",
                ),
                _stat_tile(
                    label="Completed rides with fares",
                    value=f"{revenue_metrics.completed_rides_with_fare:,}",
                    hint="Rows included in fare aggregates",
                ),
            ],
        ),
        c.Heading(text="Driver activity snapshot", level=2, class_name=H2),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Driver accounts",
                    value=f"{driver_snapshot.total_driver_accounts:,}",
                    hint="Total registered users with role=driver",
                ),
                _stat_tile(
                    label="Drivers with location",
                    value=f"{driver_snapshot.drivers_with_location:,}",
                    hint="Rows in driver_locations",
                ),
                _stat_tile(
                    label="Active in last 15m",
                    value=f"{driver_snapshot.drivers_active_last_15m:,}",
                    hint="GPS updates within 15 minutes",
                ),
                _stat_tile(
                    label="Active in last 60m",
                    value=f"{driver_snapshot.drivers_active_last_60m:,}",
                    hint="GPS updates within 60 minutes",
                ),
            ],
        ),
        c.Heading(text="Demand and cohorts", level=2, class_name=H2),
        c.Div(
            class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
            components=[
                _stat_tile(
                    label="Fruger pickup events",
                    value=f"{demand.fruger_pickups_total:,}",
                    hint="Rows in pickups where source=fruger_app",
                ),
            ],
        ),
        *status_section,
        *_metric_table("Pickup source split", demand.by_pickup_source),
        *_metric_table("Pickup demand by hour", demand.by_pickup_hour),
        *_metric_table("Pickup demand by date (last 30 days)", demand.by_pickup_date_last_30d),
        *_metric_table("Top dispatch bases", demand.top_bases),
        *_metric_table("Top geo cells (0.01 precision)", demand.top_geo_cells),
        *_metric_table("Users by role", metrics.cohorts.users_by_role),
        *_metric_table("Top riders by ride count", metrics.cohorts.top_riders_by_ride_count),
        *_metric_table("Top drivers by bid count", metrics.cohorts.top_drivers_by_bid_count),
        *build_nyc_analytics_embedded_sections(
            nyc_overview,
            nyc_error,
            request_base=request_base,
            include_reference_links=False,
        ),
        build_footer(),
    ]
    return [c.Page(class_name=PAGE, components=components)]
