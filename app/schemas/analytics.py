"""API models for NYC **pickup** analytics.

All rows live in one ``pickups`` table: historical TLC/Kaggle seed points plus one
analytics row per Fruger ride request (``source=fruger_app``). Charts aggregate both.
"""

from pydantic import BaseModel, Field


class CountByLabel(BaseModel):
    """One category and how many pickups fall in it."""

    label: str = Field(title="Category")
    count: int = Field(ge=0, title="Pickups")


class PickupTotals(BaseModel):
    """Aggregate counts for the loaded pickup rows."""

    total_pickups: int = Field(ge=0)
    pickups_with_latlon: int = Field(
        ge=0,
        description="Rows from 2014 files with latitude/longitude.",
    )
    pickups_with_zone: int = Field(
        ge=0,
        description="Rows with a TLC zone label (typically 2015 + zone lookup).",
    )
    distinct_bases: int = Field(ge=0, description="Distinct TLC base codes.")


class NycOverviewResponse(BaseModel):
    """Dashboard + JSON payload for the unified Fruger ``pickups`` stream."""

    totals: PickupTotals
    by_pickup_source: list[CountByLabel]
    by_borough: list[CountByLabel]
    by_base: list[CountByLabel]
    by_hour: list[CountByLabel]
    top_zones: list[CountByLabel]
    by_data_source: list[CountByLabel]
    pickups_by_date: list[CountByLabel]
