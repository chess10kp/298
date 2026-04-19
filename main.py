import logging
import sqlite3
from contextlib import asynccontextmanager

import app.config as app_config
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastui import AnyComponent, FastUI, prebuilt_html
from app.dashboard import build_dashboard
from app.db.migrations import migrate_db_path, operational_tables_present
from app.db.operational_seed import seed_default_accounts, seed_optional_admin
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.driver import router as driver_router
from app.routers.pages import router as pages_router
from app.routers.rider_ui import router as rider_ui_router
from app.routers.rides import router as rides_router
from app.seed import pickup_count, pickups_schema_ok, run_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = app_config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not app_config.SKIP_DATASET_SEED:
        if not db_path.exists():
            logger.info("Creating database at %s; running dataset seed.", db_path)
            run_seed(db_path)
        elif not pickups_schema_ok(db_path):
            logger.warning("pickups table schema outdated; re-seeding %s", db_path)
            run_seed(db_path)
        elif pickup_count(db_path) == 0:
            logger.warning("pickups table is empty; re-running seed for %s", db_path)
            run_seed(db_path)
        else:
            logger.info("Dataset already present at %s; skipping pickup seed.", db_path)
    else:
        logger.info("SKIP_DATASET_SEED set; skipping NYC pickup CSV seed.")

    migrate_db_path(db_path)
    logger.info("SQLite database (all app data): %s", db_path.resolve())

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        if not operational_tables_present(conn):
            logger.error(
                "Operational tables missing after migration. Expected users, rides, bids, "
                "driver_locations in %s",
                db_path.resolve(),
            )
        seed_optional_admin(conn)
        seed_default_accounts(conn)
        conn.commit()
    finally:
        conn.close()
    yield


app = FastAPI(title="Ride service & NYC pickup analytics", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(rides_router)
app.include_router(driver_router)
app.include_router(admin_router)
app.include_router(rider_ui_router)
app.include_router(analytics_router)

app.mount(
    "/static",
    StaticFiles(directory=str(app_config.ROOT / "app" / "static")),
    name="static",
)
app.include_router(pages_router)


def _dashboard() -> list[AnyComponent]:
    """Legacy FastUI JSON for NYC analytics (used by ``/api/`` shell)."""
    return build_dashboard()


@app.get("/api", response_model=FastUI, response_model_exclude_none=True)
def dashboard_no_trailing_slash() -> list[AnyComponent]:
    return _dashboard()


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def dashboard() -> list[AnyComponent]:
    return _dashboard()


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    """Serves the FastUI React bundle for client-side routes (must be registered last)."""
    return HTMLResponse(prebuilt_html(title="Ride service & NYC pickup analytics"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
