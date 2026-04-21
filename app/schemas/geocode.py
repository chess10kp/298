"""Schemas for reverse geocoding (coordinates → display label)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReverseGeocodePoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class ReverseGeocodeBatchRequest(BaseModel):
    points: list[ReverseGeocodePoint] = Field(
        default_factory=list,
        max_length=48,
        description="Lat/lng pairs to resolve; duplicates are deduplicated server-side.",
    )


class ReverseGeocodeBatchResponse(BaseModel):
    labels: dict[str, str | None] = Field(
        default_factory=dict,
        description='Map of "lat,lng" (5 decimal places) to display name or null.',
    )
