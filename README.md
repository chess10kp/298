# FRUGER
### Ridesharing, Reimagined.
**Product Requirements Document**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Personas](#3-user-personas)
4. [Feature Requirements](#4-feature-requirements)
5. [Architecture & Technology Stack](#5-architecture--technology-stack)
6. [Database Schema](#6-database-schema)
7. [API Endpoint Summary](#7-api-endpoint-summary)
8. [Development Milestones](#8-development-milestones)
9. [Open Questions & Risks](#9-open-questions--risks)

---

## 1. Executive Summary

Fruger is a full-stack ridesharing platform designed to disrupt the traditional ridesharing model by eliminating excessive platform fees. Where incumbent platforms take up to 30% of every fare, Fruger operates on a leaner commission structure — returning more value to drivers and delivering lower prices to riders.

The platform replicates the core functionality of a production-grade ridesharing app and layers on a real-time bidding system, geolocation-powered driver routing, and rich admin analytics — all seeded with authentic Uber ride data to simulate realistic, high-load conditions from day one.

> **Mission:** To make ridesharing equitable — giving drivers a larger cut, riders a lower fare, and removing the middleman's outsized take.

### 1.1 Problem Statement

Current ridesharing platforms extract 25–30% of every fare as a platform fee. Drivers are squeezed, riders pay more than necessary, and neither party has meaningful leverage. Fruger addresses this by:

- Reducing the platform commission to a sustainable minimum
- Introducing a transparent bidding system where drivers can compete on price
- Giving both riders and drivers full visibility into pricing and routing

### 1.2 Success Metrics

| Metric | Target (6 months post-launch) |
|---|---|
| Driver commission rate | ≥ 80% of fare retained by driver |
| Rider savings vs. Uber | ≥ 15% lower average fare |
| Ride completion rate | ≥ 92% |
| Bid acceptance rate | ≥ 75% of ride requests receive ≥1 bid |
| Admin dashboard uptime | 99.5% |
| Seeded rides loaded | 100% of Kaggle dataset ingested pre-launch |

---

## 2. Goals & Non-Goals

### 2.1 Goals

1. Deliver a full authentication system supporting riders, drivers, and admins with role-based access.
2. Build a real-time ride request and bidding system with driver geolocation via Google Maps API.
3. Provide an admin analytics dashboard backed by seeded, realistic Uber ride data.
4. Design a database schema that accurately models users, rides, and bids — extensible for future features.
5. Seed the database with the Kaggle Uber Ride Analytics dataset to simulate production-level data volume from day one.
6. Support high-load simulation scenarios for performance testing.

### 2.2 Non-Goals

- Payment processing integration (e.g. Stripe, PayPal) — fares are tracked in the DB but no real-money transactions occur in v1.
- Native iOS or Android apps — Fruger v1 is a web-only platform.
- Driver background check or vehicle verification workflows.
- Surge pricing or dynamic fare multipliers.
- Customer support tooling or dispute resolution flows.

---

## 3. User Personas

### 3.1 Rider

> **Who:** Anyone who needs a ride. Creates an account, requests rides, reviews bids, and confirms a driver.

**Key needs:**
- Simple ride request flow with clear pickup and dropoff entry
- Transparent view of driver bids and pricing
- Ability to cancel a ride before a driver is confirmed
- Ride history for reference

### 3.2 Driver (Rideshare Partner)

> **Who:** Independent contractors who sign up to accept ride requests. They geolocate to riders and compete via bids.

**Key needs:**
- Real-time view of nearby ride requests on a map
- Ability to place a bid with a custom fare amount
- Turn-by-turn routing to pickup location via Google Maps
- Clear earnings summary after each completed ride

### 3.3 Admin

> **Who:** Internal platform operators. Log in via a privileged account to access the admin dashboard.

**Key needs:**
- Aggregate statistics: total rides, revenue, active users, driver supply
- Time-series charts showing ride volume and revenue trends
- Drill-down into individual rides and users
- Data powered by the seeded Kaggle dataset for realistic baseline analytics

---

## 4. Feature Requirements

### 4.1 Feature Summary

| Feature | Description | Priority | Owner |
|---|---|---|---|
| Authentication | Login, registration, role-based session management | P0 | All |
| Ride Request | Riders create and cancel ride requests | P0 | RideService |
| Driver Bidding | Drivers place fare bids on open requests | P0 | BiddingService |
| Geolocation | Google Maps routing from driver to pickup | P0 | BiddingService |
| Admin Dashboard | Charts and stats for platform admins | P1 | AdminService |
| Data Seeding | Load Kaggle dataset into DB on first run | P1 | DBSession |
| Ride History | Riders and drivers view past rides | P1 | RideService |
| High-Load Sim | Simulate concurrent ride requests | P2 | Infra |

### 4.2 Authentication (AuthService)

`AuthService` is a React context that wraps the entire frontend, exposing the current user's authentication state, role, and session token to all child components.

**Functional requirements:**

1. Users register with name, email, password, and a role selection (Rider or Driver).
2. Admins are provisioned directly in the database; no self-serve admin registration.
3. On login, the server returns a signed JWT containing user ID and role.
4. `AuthService` stores the JWT in memory and attaches it as a Bearer token to all API requests.
5. Protected routes (rider dashboard, driver dashboard, admin panel) redirect unauthenticated users to the login page.
6. Sessions expire after 24 hours; users are prompted to re-authenticate.

### 4.3 Ride Request & Cancellation (RideService)

1. Authenticated riders can submit a ride request specifying a pickup location and a destination.
2. A new ride record is created in the Rides table with status `OPEN`.
3. Open rides are broadcast to nearby drivers (within a configurable radius).
4. Riders can cancel any ride with status `OPEN` or `BIDDING` at no penalty.
5. Rides move through the following status lifecycle: `OPEN` → `BIDDING` → `CONFIRMED` → `IN_PROGRESS` → `COMPLETED` (or `CANCELLED`).

### 4.4 Bidding System (BiddingService)

1. Drivers see a live feed of `OPEN` ride requests within their proximity.
2. A driver places a bid by specifying a fare amount. Multiple drivers can bid on the same ride.
3. The rider reviews all bids, seeing the driver's distance from pickup, estimated arrival time, and bid amount.
4. The rider accepts one bid; all other bids are automatically declined and drivers are notified.
5. Once a bid is accepted, the ride moves to `CONFIRMED` and the winning driver receives the pickup route via Google Maps.
6. `BiddingService` expires bids that go unacknowledged for more than 10 minutes.

### 4.5 Geolocation & Routing

Fruger integrates the Google Maps JavaScript API and the Directions API to provide real-time routing for drivers.

- Driver location is polled every 5 seconds using the browser Geolocation API.
- Distance from each driver to each open ride's pickup location is computed server-side to avoid exposing all driver positions to riders.
- On bid acceptance, the driver's frontend renders a turn-by-turn directions overlay from their current position to the rider's pickup address.
- An ETA estimate is shown to the rider, updated as the driver moves.

### 4.6 Admin Dashboard (AdminService)

`AdminService` aggregates data from `DBSession` and exposes endpoints that power the admin frontend. Data is prepared server-side with Pandas and rendered on the frontend.

**Dashboard panels:**
- Total rides, revenue, active users, and registered drivers (summary cards)
- Ride volume over time (line chart, filterable by date range)
- Revenue by day / week / month (bar chart)
- Ride status distribution: `COMPLETED` vs. `CANCELLED` vs. `IN_PROGRESS` (pie/donut chart)
- Top pickup and drop-off zones (map heatmap via Google Maps)
- Driver earnings leaderboard (sortable table)

### 4.7 Data Seeding

> **Dataset:** Kaggle — [Uber Ride Analytics Dashboard](https://www.kaggle.com/datasets/yashdevladdha/uber-ride-analytics-dashboard)

The seed script runs once at first boot and populates the database before any real users interact with the system. The seeded data provides the admin dashboard with a realistic, varied baseline of rides spanning multiple years, cities, and fare ranges.

1. The seed script is idempotent: re-running it on a populated database is a no-op.
2. Seeded users are flagged with `is_seeded = true` and are excluded from the live ride request queue.
3. Seeded rides are pre-assigned statuses of `COMPLETED` or `CANCELLED` to reflect historical data.

---

## 5. Architecture & Technology Stack

### 5.1 Technology Choices

| Layer | Technology |
|---|---|
| Frontend | FastUI (component framework built on FastAPI) |
| Backend / API | FastAPI (Python) |
| Data Layer | DBSession (SQLAlchemy ORM abstraction) |
| Data Visualization | Pandas (server-side aggregation), Chart.js or Plotly (frontend rendering) |
| Geolocation | Google Maps JavaScript API, Directions API, Geolocation API |
| Authentication | JWT via python-jose / PyJWT |
| Database | PostgreSQL (production), SQLite (local dev) |
| Dataset | Kaggle: Uber Ride Analytics Dashboard |

### 5.2 Service Architecture

#### AuthService (Context Provider)

| Member | Type | Description |
|---|---|---|
| `currentUser` | `User \| None` | The currently authenticated user object |
| `isAuthenticated` | `bool` | Whether a valid session token is present |
| `role` | `enum` | `RIDER`, `DRIVER`, or `ADMIN` — gates UI access |
| `login(email, pw)` | method | Validates credentials, stores JWT, updates context |
| `logout()` | method | Clears JWT and resets state |

#### DBSession (Data Access Layer)

| Member | Type | Description |
|---|---|---|
| `users_table` | `Table` | ORM-mapped Users table |
| `rides_table` | `Table` | ORM-mapped Rides table |
| `bids_table` | `Table` | ORM-mapped Bids table |
| `get_session()` | method | Returns a scoped SQLAlchemy session |
| `seed()` | method | Idempotent seed from Kaggle CSV |

#### RideService

| Member | Type | Description |
|---|---|---|
| `create_ride(user, from, to)` | method | Creates a new `OPEN` ride record |
| `cancel_ride(ride_id)` | method | Sets ride status to `CANCELLED` |
| `get_ride_history(user_id)` | method | Returns all rides for a user |
| `update_status(ride_id, status)` | method | Transitions ride through status lifecycle |

#### AdminService

| Member | Type | Description |
|---|---|---|
| `get_summary_stats()` | method | Returns aggregate KPI numbers |
| `get_ride_volume(start, end)` | method | Time-series ride count for date range |
| `get_revenue_series(granularity)` | method | Revenue bucketed by day/week/month |
| `get_top_zones()` | method | Top pickup/dropoff coordinates |
| `get_driver_earnings()` | method | Per-driver earnings leaderboard |

#### BiddingService

| Member | Type | Description |
|---|---|---|
| `open_ride_feed(driver_id)` | method | Returns `OPEN` rides near the driver |
| `place_bid(driver_id, ride_id, fare)` | method | Creates a Bid record |
| `accept_bid(bid_id)` | method | Confirms a driver, declines all other bids |
| `expire_stale_bids()` | method | Marks bids older than 10 min as `EXPIRED` |
| `route_driver(bid_id)` | method | Returns Google Maps directions payload |

---

## 6. Database Schema

### 6.1 Users

| Field | Type | Description |
|---|---|---|
| `id` | `int (PK)` | Auto-incrementing primary key |
| `name` | `str` | Full display name |
| `email` | `str (unique)` | Login credential, must be unique |
| `password_hash` | `str` | Bcrypt-hashed password |
| `role` | `enum` | `RIDER`, `DRIVER`, or `ADMIN` |
| `is_seeded` | `bool` | True if row originates from Kaggle seed |
| `created_at` | `datetime` | Account creation timestamp |

### 6.2 Rides

| Field | Type | Description |
|---|---|---|
| `id` | `int (PK)` | Auto-incrementing primary key |
| `rider_id` | `int (FK → users)` | The user who requested the ride |
| `driver_id` | `int (FK → users, nullable)` | Assigned after bid acceptance |
| `fare` | `decimal` | Final agreed fare (from winning bid) |
| `from_location` | `str` | Pickup address or coordinate string |
| `to_location` | `str` | Dropoff address or coordinate string |
| `status` | `enum` | `OPEN`, `BIDDING`, `CONFIRMED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `is_seeded` | `bool` | True if row originates from Kaggle seed |
| `created_at` | `datetime` | Ride request timestamp |
| `completed_at` | `datetime (nullable)` | Ride completion timestamp |

### 6.3 Bids

| Field | Type | Description |
|---|---|---|
| `id` | `int (PK)` | Auto-incrementing primary key |
| `ride_id` | `int (FK → rides)` | The ride being bid on |
| `driver_id` | `int (FK → users)` | The driver placing the bid |
| `fare_amount` | `decimal` | The driver's proposed fare |
| `distance_to_pickup_km` | `decimal` | Driver's distance from pickup at bid time |
| `eta_minutes` | `int` | Estimated arrival time at bid placement |
| `status` | `enum` | `PENDING`, `ACCEPTED`, `DECLINED`, `EXPIRED` |
| `created_at` | `datetime` | Bid placement timestamp |

---

## 7. API Endpoint Summary


All endpoints are prefixed with `/api/v1`. All non-public endpoints require a valid `Bearer` token in the `Authorization` header.

Note: the codebase uses specific enum names and paths; the table below reflects the current implementation.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register a new rider or driver |
| `POST` | `/api/v1/auth/token` | Public | OAuth2 token endpoint (use `username` as email) |
| `POST` | `/api/v1/auth/session` | Public | Session login that sets httpOnly cookie |
| `GET` | `/api/v1/rides/me` | Rider | List rider's own rides |
| `POST` | `/api/v1/rides` | Rider | Create a new ride request |
| `POST` | `/api/v1/rides/{id}/cancel` | Rider | Cancel an open ride |
| `GET` | `/api/v1/rides/open` | Driver | View open rides available for bidding |
| `POST` | `/api/v1/rides/{id}/bids` | Driver | Place a bid on a ride |
| `POST` | `/api/v1/rides/{ride_id}/bids/{bid_id}/accept` | Rider | Accept a driver's bid |
| `GET` | `/api/v1/rides/bids/{bid_id}/route` | Driver | Mocked routing payload from driver to pickup |
| `GET` | `/api/v1/admin/stats` | Admin | Aggregate KPI summary |
| `GET` | `/api/v1/admin/plots/revenue.png` | Admin | Revenue plot (PNG) |
| `GET` | `/api/v1/admin/driver-locations` | Admin | Current driver locations with email |

---

## 8. Development Milestones

| Milestone | Scope | Deliverable | Target |
|---|---|---|---|
| M1 | DB schema, DBSession, seed script | Database populated with Kaggle data | Week 2 |
| M2 | AuthService, login/register UI | Working auth with role-based routing | Week 3 |
| M3 | RideService, ride request + cancel | Riders can create and cancel rides | Week 4 |
| M4 | BiddingService, Google Maps routing | Drivers bid; rider accepts; driver routed | Week 6 |
| M5 | AdminService + dashboard UI | Admin can view charts and KPIs | Week 7 |
| M6 | High-load simulation + bug fixes | Platform tested under simulated load | Week 8 |

---

## 9. Open Questions & Risks

### 9.1 Open Questions

1. What is the target commission rate for Fruger? This needs to be defined before fare calculation logic is implemented in `BiddingService`.
2. Should drivers be able to see competing bids, or only their own? Transparency vs. race-to-the-bottom dynamics.
3. What database will be used in production? PostgreSQL is recommended but SQLite may suffice for local dev and simulation.
4. Should `from_location` and `to_location` store raw strings, or structured coordinate data? The latter is required for the heatmap and distance calculations.
5. Is a websocket layer needed for real-time bid updates, or will polling suffice for v1?

### 9.2 Risks

> **⚠️ Google Maps API costs** — Costs can escalate quickly with frequent geolocation polling. Set quotas and monitor usage from day one.

> **⚠️ Kaggle data quality** — The dataset may contain missing or malformed location data. The seed script must validate and clean records before insert.

> **⚠️ FastUI ecosystem maturity** — FastUI is relatively new and has a smaller ecosystem than React/Vue. UI component gaps may require custom workarounds.

> **⚠️ Real-time polling overhead** — Without a websocket layer, real-time bid feeds rely on polling, increasing server load under high-concurrency simulation.
