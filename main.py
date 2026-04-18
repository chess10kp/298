import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastui import AnyComponent, FastUI, prebuilt_html

from app.config import DB_PATH
from app.dashboard import build_dashboard
from app.routers.analytics import router as analytics_router
from app.seed import pickup_count, pickups_schema_ok, run_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        logger.info("Creating database at %s; running seed.", DB_PATH)
        run_seed(DB_PATH)
    elif not pickups_schema_ok(DB_PATH):
        logger.warning("pickups table schema outdated; re-seeding %s", DB_PATH)
        run_seed(DB_PATH)
    elif pickup_count(DB_PATH) == 0:
        logger.warning("pickups table is empty; re-running seed for %s", DB_PATH)
        run_seed(DB_PATH)
    else:
        logger.info("Database already present at %s; skipping seed.", DB_PATH)
    yield


app = FastAPI(title="NYC Uber pickup analytics", lifespan=lifespan)
app.include_router(analytics_router)


def _dashboard() -> list[AnyComponent]:
    """FastUI loads this when the user opens ``/`` in the browser."""
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
    return HTMLResponse(prebuilt_html(title="NYC Uber pickup analytics"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
