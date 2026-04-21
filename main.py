import logging
import sqlite3
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import app.config as app_config
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.fastui_html import fruger_prebuilt_html
from app.db.migrations import migrate_db_path, operational_tables_present
from app.db.operational_seed import seed_default_accounts, seed_optional_admin
from app.operational_demo_seed import seed_operational_demo_if_empty
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.driver import router as driver_router
from app.routers.embed import router as embed_router
from app.routers.fruger_fastui import router as fruger_fastui_router
from app.routers.pages import router as pages_router
from app.routers.rider_ui import router as rider_ui_router
from app.routers.rides import router as rides_router
from app.seed import pickup_count, pickups_schema_ok, run_seed
from app.services.db_session import DBSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/auth_debug.log"), logging.StreamHandler()],
)
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
    conn.row_factory = sqlite3.Row
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
        seed_operational_demo_if_empty(conn)
        conn.commit()
    finally:
        conn.close()
    # start background scheduler to expire stale bids every minute
    sched = AsyncIOScheduler()

    def _expire():
        db = DBSession(app_config.DB_PATH)
        with db.connection() as conn:
            n = db.expire_stale_bids(conn, older_than_minutes=10)
            if n:
                logging.getLogger(__name__).info("Expired %s stale bids", n)

    sched.add_job(
        _expire, IntervalTrigger(seconds=60), id="expire_bids", replace_existing=True
    )
    sched.start()

    try:
        yield
    finally:
        try:
            sched.shutdown(wait=False)
        except Exception:
            logging.getLogger(__name__).exception("Failed to shutdown scheduler")


app = FastAPI(title="Fruger — rides & NYC pickup analytics", lifespan=lifespan)

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
app.include_router(embed_router)
app.include_router(fruger_fastui_router)
app.include_router(pages_router)


# Scheduler is started inside the lifespan context to avoid FastAPI on_event deprecation.


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    """Serves the FastUI React bundle for client-side routes (must be registered last)."""
    return HTMLResponse(
        fruger_prebuilt_html(title="Fruger — rides & NYC pickup analytics")
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
