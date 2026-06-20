"""FastAPI application entrypoint."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.exceptions import AppException
from app.limiter import limiter
from app.routers import auth, dashboard, evaluations, submissions
from app.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(submissions.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.on_event("startup")
def _on_startup() -> None:
    """Start the background Google Forms sync scheduler."""
    start_scheduler()


@app.on_event("shutdown")
def _on_shutdown() -> None:
    """Stop the background scheduler cleanly."""
    stop_scheduler()


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convert any AppException subclass into a consistent JSON error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.get("/health")
async def health():
    return {"status": "healthy"}
