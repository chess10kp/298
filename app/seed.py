"""Load FiveThirtyEight / Kaggle NYC Uber **pickup** CSVs into SQLite.

2014 monthly files: ``Date/Time``, ``Lat``, ``Lon``, ``Base`` (TLC base code).
2015 file (optional): ``Pickup_date``, ``locationID``, ``Dispatching_base_num`` + ``taxi-zone-lookup.csv``.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from app.config import CSV_FALLBACK, KAGGLE_DATASET_SLUG, KAGGLE_DATASET_URL, NYC_LOAD_2015

logger = logging.getLogger(__name__)

PICKUPS_TABLE = "pickups"

_PICKUPS_DDL = f"""CREATE TABLE {PICKUPS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pickup_datetime TEXT,
    pickup_date TEXT,
    pickup_hour INTEGER,
    lat REAL,
    lon REAL,
    location_id INTEGER,
    zone TEXT,
    borough TEXT,
    base_code TEXT,
    data_source TEXT
)"""


def pickups_schema_ok(db_path: Path) -> bool:
    """Return False if ``pickups`` is missing or does not match the NYC ingest schema."""
    if not db_path.is_file():
        return False
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (PICKUPS_TABLE,),
        )
        if cur.fetchone() is None:
            return False
        cur.execute(f"PRAGMA table_info({PICKUPS_TABLE})")
        cols = {row[1] for row in cur.fetchall()}
        required = {"pickup_datetime", "pickup_hour", "base_code", "data_source"}
        return required.issubset(cols)
    finally:
        conn.close()


def rides_schema_ok(db_path: Path) -> bool:
    """Deprecated name — use :func:`pickups_schema_ok`. Kept for import stability."""
    return pickups_schema_ok(db_path)


def pickup_count(db_path: Path) -> int:
    """Number of rows in ``pickups`` (0 if missing or error)."""
    if not db_path.is_file():
        return 0
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {PICKUPS_TABLE}")
        return int(cur.fetchone()[0])
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def _find_zone_lookup(root: Path) -> Path | None:
    for name in ("taxi-zone-lookup.csv", "taxi_zone_lookup.csv"):
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None


def _read_zone_lookup(path: Path) -> pd.DataFrame:
    z = pd.read_csv(path)
    z.columns = [str(c).strip().lower().replace(" ", "_") for c in z.columns]
    id_col = next((c for c in z.columns if "location" in c and "id" in c), None)
    if id_col is None:
        for c in z.columns:
            if c in ("locationid", "location_id"):
                id_col = c
                break
    if id_col is None:
        raise ValueError(f"Could not find LocationID column in {path}")
    zone_col = next((c for c in z.columns if c == "zone"), None)
    bor_col = next((c for c in z.columns if "borough" in c), None)
    out = z[[id_col]].copy()
    out.columns = ["location_id"]
    out["zone"] = z[zone_col] if zone_col else None
    out["borough"] = z[bor_col] if bor_col else None
    out["location_id"] = pd.to_numeric(out["location_id"], errors="coerce").astype("Int64")
    return out.drop_duplicates("location_id", keep="first")


def _month_order_2014() -> list[str]:
    return ["apr14", "may14", "jun14", "jul14", "aug14", "sep14"]


def _find_2014_csvs(root: Path) -> list[Path]:
    """Discover 2014 Uber monthly files (case-insensitive; Kaggle zips vary by platform)."""
    candidates: list[Path] = []
    for p in root.rglob("*.csv"):
        name = p.name.lower()
        if not name.startswith("uber-raw-data-"):
            continue
        if "janjune" in name:
            continue
        # e.g. uber-raw-data-apr14.csv — must end with 14.csv, not 15.csv
        if not name.endswith("14.csv"):
            continue
        candidates.append(p)

    order = {f"uber-raw-data-{m}.csv": i for i, m in enumerate(_month_order_2014())}

    def sort_key(path: Path) -> tuple[int, str]:
        key = path.name.lower()
        return (order.get(key, 100), str(path))

    candidates.sort(key=sort_key)
    if candidates:
        logger.info(
            "Found %s 2014 Uber CSV(s): %s",
            len(candidates),
            [p.name for p in candidates],
        )
    return candidates


def _find_2015_csv(root: Path) -> Path | None:
    for p in root.rglob("*.csv"):
        n = p.name.lower()
        if "janjune" in n and "15" in n and "uber-raw-data" in n:
            logger.info("Found 2015 Uber CSV: %s", p.name)
            return p
    return None


def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lstrip("\ufeff").strip() for c in df.columns]
    return df


def _normalize_2014(df: pd.DataFrame) -> pd.DataFrame:
    """Map 2014 TLC columns to ``pickups`` dataframe columns."""
    df = _clean_column_names(df)
    lower = {c.lower(): c for c in df.columns}
    dt_col = lower.get("date/time") or lower.get("datetime")
    if dt_col is None:
        for c in df.columns:
            cl = c.lower().replace(" ", "")
            if "date" in cl and "time" in cl:
                dt_col = c
                break
    lat_c = lower.get("lat") or lower.get("latitude")
    lon_c = lower.get("lon") or lower.get("lng") or lower.get("longitude")
    base_c = lower.get("base")
    if not all([dt_col, lat_c, lon_c, base_c]):
        raise ValueError(
            f"Expected Date/Time, Lat, Lon, Base columns; got {list(df.columns)}"
        )

    dt = pd.to_datetime(df[dt_col], errors="coerce", utc=False)
    ok = dt.notna()
    if not ok.any():
        return pd.DataFrame(
            columns=[
                "pickup_datetime",
                "pickup_date",
                "pickup_hour",
                "lat",
                "lon",
                "location_id",
                "zone",
                "borough",
                "base_code",
                "data_source",
            ]
        )
    df = df.loc[ok].reset_index(drop=True)
    dt = dt.loc[ok].reset_index(drop=True)
    return pd.DataFrame(
        {
            "pickup_datetime": dt.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "pickup_date": dt.dt.strftime("%Y-%m-%d"),
            "pickup_hour": dt.dt.hour,
            "lat": pd.to_numeric(df[lat_c], errors="coerce"),
            "lon": pd.to_numeric(df[lon_c], errors="coerce"),
            "location_id": pd.NA,
            "zone": pd.NA,
            "borough": pd.NA,
            "base_code": df[base_c].astype(str),
            "data_source": "2014",
        }
    )


def _normalize_2015(df: pd.DataFrame, zones: pd.DataFrame) -> pd.DataFrame:
    """Map 2015 TLC columns + zone lookup to ``pickups`` dataframe columns."""
    df = _clean_column_names(df)
    lower = {c.lower(): c for c in df.columns}
    pu = lower.get("pickup_date") or lower.get("pickup_datetime")
    loc = lower.get("locationid") or lower.get("location_id")
    base = lower.get("dispatching_base_num") or lower.get("base")
    if not all([pu, loc, base]):
        raise ValueError(
            "Expected Pickup_date, locationID, Dispatching_base_num in 2015 Uber CSV"
        )

    dt = pd.to_datetime(df[pu], errors="coerce", utc=False)
    ok = dt.notna()
    if not ok.any():
        return pd.DataFrame(
            columns=[
                "pickup_datetime",
                "pickup_date",
                "pickup_hour",
                "lat",
                "lon",
                "location_id",
                "zone",
                "borough",
                "base_code",
                "data_source",
            ]
        )
    df = df.loc[ok].reset_index(drop=True)
    dt = dt.loc[ok].reset_index(drop=True)
    lid = pd.to_numeric(df[loc], errors="coerce").astype("Int64")
    tmp = pd.DataFrame({"location_id": lid})
    merged = tmp.merge(zones, on="location_id", how="left")
    return pd.DataFrame(
        {
            "pickup_datetime": dt.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "pickup_date": dt.dt.strftime("%Y-%m-%d"),
            "pickup_hour": dt.dt.hour,
            "lat": pd.NA,
            "lon": pd.NA,
            "location_id": lid,
            "zone": merged["zone"],
            "borough": merged["borough"],
            "base_code": df[base].astype(str),
            "data_source": "2015",
        }
    )


def _append_dataframe(conn: sqlite3.Connection, df: pd.DataFrame, *, first: bool) -> None:
    df.to_sql(PICKUPS_TABLE, conn, if_exists="replace" if first else "append", index=False)


def _download_kaggle_root() -> Path | None:
    try:
        import kagglehub
    except ImportError:
        logger.warning("kagglehub is not installed; skipping Kaggle download.")
        return None
    try:
        logger.info("Downloading Kaggle dataset %s (%s)", KAGGLE_DATASET_SLUG, KAGGLE_DATASET_URL)
        base = Path(kagglehub.dataset_download(KAGGLE_DATASET_SLUG))
        logger.info("Kaggle dataset downloaded to %s", base)
        return base
    except Exception as e:
        logger.warning("Kaggle dataset download failed: %s", e)
        return None


def _seed_from_root(conn: sqlite3.Connection, root: Path) -> bool:
    zones_df: pd.DataFrame | None = None
    zpath = _find_zone_lookup(root)
    if zpath is not None:
        try:
            zones_df = _read_zone_lookup(zpath)
            logger.info("Loaded TLC zone lookup from %s (%s rows)", zpath, len(zones_df))
        except Exception as e:
            logger.warning("Could not load zone lookup %s: %s", zpath, e)

    files_2014 = _find_2014_csvs(root)
    if not files_2014:
        all_csv = sorted(root.rglob("*.csv"))
        logger.warning(
            "No 2014 Uber monthly CSVs matched under %s. Found %s CSV(s) total (sample: %s).",
            root,
            len(all_csv),
            [p.name for p in all_csv[:12]],
        )
        return False

    first = True
    chunksize = 200_000
    read_kw: dict = {"chunksize": chunksize, "encoding": "utf-8-sig", "low_memory": False}
    for fp in files_2014:
        logger.info("Loading %s", fp)
        try:
            for chunk in pd.read_csv(fp, **read_kw):
                try:
                    norm = _normalize_2014(chunk)
                except Exception as e:
                    logger.exception("Failed to normalize chunk from %s: %s", fp.name, e)
                    continue
                if norm.empty:
                    continue
                _append_dataframe(conn, norm, first=first)
                first = False
        except Exception as e:
            logger.exception("Failed to read %s: %s", fp, e)
            continue

    if NYC_LOAD_2015 and zones_df is not None:
        p15 = _find_2015_csv(root)
        if p15 is not None:
            logger.info("Loading 2015 pickups from %s (large file)", p15.name)
            for chunk in pd.read_csv(p15, **read_kw):
                try:
                    norm = _normalize_2015(chunk, zones_df)
                except Exception as e:
                    logger.exception("Failed to normalize 2015 chunk: %s", e)
                    continue
                if norm.empty:
                    continue
                _append_dataframe(conn, norm, first=first)
                first = False
        else:
            logger.warning("NYC_LOAD_2015 is True but uber-raw-data-janjune-15.csv not found.")
    elif NYC_LOAD_2015 and zones_df is None:
        logger.warning("NYC_LOAD_2015 is True but zone lookup missing; skipping 2015.")

    if first:
        logger.warning("No pickup rows were written from NYC CSV files.")
        return False
    return True


def run_seed(db_path: Path) -> None:
    """Drop legacy tables, then load NYC CSVs into ``pickups``."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS rides")
        cur.execute(f"DROP TABLE IF EXISTS {PICKUPS_TABLE}")
        conn.commit()

        root = _download_kaggle_root()
        loaded = False
        if root is not None:
            loaded = _seed_from_root(conn, root)

        if not loaded and CSV_FALLBACK.is_file():
            logger.info("Using fallback CSV at %s", CSV_FALLBACK)
            first = True
            fb_kw = {"chunksize": 200_000, "encoding": "utf-8-sig", "low_memory": False}
            for chunk in pd.read_csv(CSV_FALLBACK, **fb_kw):
                try:
                    norm = _normalize_2014(chunk)
                except Exception as e:
                    logger.exception("Failed to normalize fallback chunk: %s", e)
                    continue
                if norm.empty:
                    continue
                _append_dataframe(conn, norm, first=first)
                first = False
            loaded = not first

        if not loaded:
            logger.warning(
                "No NYC Uber CSV available (Kaggle failed and no file at %s); "
                "creating empty pickups table.",
                CSV_FALLBACK,
            )
            cur.execute(_PICKUPS_DDL)
            conn.commit()
            return

        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {PICKUPS_TABLE}")
        n = cur.fetchone()[0]
        logger.info("Loaded %s pickup rows into %s.", n, PICKUPS_TABLE)
    finally:
        conn.close()
