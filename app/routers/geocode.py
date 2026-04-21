"""Authenticated reverse geocoding for ride UIs."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser
from app.schemas.geocode import (
    ReverseGeocodeBatchRequest,
    ReverseGeocodeBatchResponse,
)
from app.services.reverse_geocode import batch_reverse_labels

router = APIRouter(prefix="/api/v1/geocode", tags=["geocode"])


@router.post("/reverse-batch", response_model=ReverseGeocodeBatchResponse)
def reverse_geocode_batch(
    body: ReverseGeocodeBatchRequest,
    _: CurrentUser,
) -> ReverseGeocodeBatchResponse:
    pts = [(p.lat, p.lng) for p in body.points]
    labels = batch_reverse_labels(pts)
    return ReverseGeocodeBatchResponse(labels=labels)
