"""Pydantic models for ride-hailing API."""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    rider = "rider"
    driver = "driver"
    admin = "admin"


class RideStatus(str, Enum):
    bidding_open = "bidding_open"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class BidStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class UserPublic(BaseModel):
    id: int
    email: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.rider


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RideCreate(BaseModel):
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lng: float = Field(ge=-180, le=180)
    dropoff_lat: float = Field(ge=-90, le=90)
    dropoff_lng: float = Field(ge=-180, le=180)


class RideOut(BaseModel):
    id: int
    rider_id: int
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    status: RideStatus
    accepted_bid_id: int | None
    final_fare_cents: int | None
    created_at: str
    cancelled_at: str | None
    completed_at: str | None


class BidOut(BaseModel):
    id: int
    ride_id: int
    driver_id: int
    fare_cents: int
    distance_to_pickup_m: float
    status: BidStatus
    created_at: str


class BidPlaceRequest(BaseModel):
    fare_cents: int = Field(gt=0)


class DriverLocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class AdminStatsOut(BaseModel):
    total_rides: int
    rides_by_status: dict[str, int]
    completed_revenue_cents: int
    total_bids: int


class DriverLocationOut(BaseModel):
    driver_id: int
    email: str
    lat: float
    lng: float
    updated_at: str


class BidderLocationOut(BaseModel):
    driver_id: int
    lat: float
    lng: float
