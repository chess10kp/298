"""Application paths and dataset configuration.

Kaggle downloads require authentication outside Kaggle notebooks:
  - Run ``kagglehub.login()`` once, or
  - Set ``KAGGLE_API_TOKEN``, or
  - Place credentials under ``~/.kaggle/`` per https://github.com/Kaggle/kagglehub

If download fails (offline / no token), seed falls back to a local CSV under ``data/`` if present.

**Dataset:** FiveThirtyEight — Uber pickups in New York City (US geography, lat/lon in 2014 files).

**Storage:** ``fruger.db`` table ``pickups`` — one row per TLC pickup event (not a full trip record).
"""

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
