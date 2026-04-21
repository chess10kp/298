"""Pydantic models for derived admin analytics metrics."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LabeledCount(BaseModel):
    label: str
    count: int = Field(ge=0)


class FunnelMetrics(BaseModel):
    total_rides: int = Field(ge=0)
    bidding_open: int = Field(ge=0)
    assigned: int = Field(ge=0)
    in_progress: int = Field(ge=0)
    completed: int = Field(ge=0)
    cancelled: int = Field(ge=0)
    assign_rate: float = Field(ge=0.0, le=1.0)
    completion_rate: float = Field(ge=0.0, le=1.0)
    cancellation_rate: float = Field(ge=0.0, le=1.0)


class RevenueFareMetrics(BaseModel):
    completed_revenue_cents: int = Field(ge=0)
    completed_rides_with_fare: int = Field(ge=0)
    avg_completed_fare_cents: int = Field(ge=0)
    median_completed_fare_cents: int = Field(ge=0)
    accepted_bid_count: int = Field(ge=0)
    avg_accepted_bid_cents: int = Field(ge=0)
    median_accepted_bid_cents: int = Field(ge=0)
    paired_completed_with_accepted_bid: int = Field(ge=0)
    avg_final_minus_accepted_cents: int = Field(ge=0)


class BidMarketMetrics(BaseModel):
    total_bids: int = Field(ge=0)
    rides_with_bids: int = Field(ge=0)
    rides_with_zero_bids: int = Field(ge=0)
    avg_bids_per_ride: float = Field(ge=0.0)
    median_bids_per_ride: float = Field(ge=0.0)
    accepted_bids: int = Field(ge=0)
    rejected_bids: int = Field(ge=0)
    pending_bids: int = Field(ge=0)
    bid_acceptance_rate: float = Field(ge=0.0, le=1.0)
    distinct_bidding_drivers: int = Field(ge=0)


class DriverSnapshotMetrics(BaseModel):
    total_driver_accounts: int = Field(ge=0)
    drivers_with_location: int = Field(ge=0)
    drivers_active_last_15m: int = Field(ge=0)
    drivers_active_last_60m: int = Field(ge=0)


class DemandMetrics(BaseModel):
    fruger_pickups_total: int = Field(ge=0)
    by_pickup_source: list[LabeledCount]
    by_pickup_hour: list[LabeledCount]
    by_pickup_date_last_30d: list[LabeledCount]
    top_bases: list[LabeledCount]
    top_geo_cells: list[LabeledCount]


class CohortMetrics(BaseModel):
    users_by_role: list[LabeledCount]
    top_riders_by_ride_count: list[LabeledCount]
    top_drivers_by_bid_count: list[LabeledCount]


class AdminMetricsOut(BaseModel):
    demand: DemandMetrics
    funnel: FunnelMetrics
    revenue_fares: RevenueFareMetrics
    bid_market: BidMarketMetrics
    driver_snapshot: DriverSnapshotMetrics
    cohorts: CohortMetrics
