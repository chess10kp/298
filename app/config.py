"""Application paths and dataset configuration.

Kaggle downloads require authentication outside Kaggle notebooks:
  - Run ``kagglehub.login()`` once, or
  - Set ``KAGGLE_API_TOKEN``, or
  - Place credentials under ``~/.kaggle/`` per https://github.com/Kaggle/kagglehub

If download fails (offline / no token), seed falls back to a local CSV under ``data/`` if present.

**Dataset:** FiveThirtyEight — Uber pickups in New York City (US geography, lat/lon in 2014 files).

**Storage:** ``fruger.db`` table ``pickups`` — one row per TLC pickup event (not a full trip record).
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "fruger.db"
DATA_DIR = ROOT / "data"

# https://www.kaggle.com/datasets/fivethirtyeight/uber-pickups-in-new-york-city
KAGGLE_DATASET_URL = (
    "https://www.kaggle.com/datasets/fivethirtyeight/uber-pickups-in-new-york-city"
)
KAGGLE_DATASET_SLUG = "fivethirtyeight/uber-pickups-in-new-york-city"

# Manual fallback: one 2014 monthly file (same schema as Kaggle bundle)
CSV_FALLBACK = DATA_DIR / "uber-raw-data-apr14.csv"

# Jan–Jun 2015 file is very large (~20M rows); set True to load it after 2014 files
NYC_LOAD_2015 = False

# Auth / operational ride-hailing
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
# Optional first-time admin (set in .env); hashed at seed time
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Created on startup if no user with that email exists (fresh DB / after delete)
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@local.dev")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Adminpass123")
DEFAULT_RIDER_EMAIL = os.getenv("DEFAULT_RIDER_EMAIL", "rider@local.dev")
DEFAULT_RIDER_PASSWORD = os.getenv("DEFAULT_RIDER_PASSWORD", "Riderpass123")

# Show default emails/passwords on /login (set false in production)
SHOW_DEFAULT_ACCOUNT_HINTS = os.getenv("SHOW_DEFAULT_ACCOUNT_HINTS", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Tests / minimal environments: skip FiveThirtyEight pickup CSV seed (operational tables still migrate)
SKIP_DATASET_SEED = os.getenv("SKIP_DATASET_SEED", "").lower() in ("1", "true", "yes")
