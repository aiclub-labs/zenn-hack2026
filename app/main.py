from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.hello_agent import run_hello_agent
from app.api import citations as citations_router
from app.api import hearout as hearout_router
from app.api import retrieval as retrieval_router
from app.api import reviews as reviews_router
from app.api import turn as turn_router
from app.config import settings

# WT-C owns app.api.schemas; import lazily so its absence doesn't break boot.
try:
    from app.api import schemas as schemas_router  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    schemas_router = None  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.applicationinsights_connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string
        )
    # End-of-day merge: wire WT-B/C/D real instances into WT-E _deps setters.
    from app.api._wiring import build_and_register

    build_and_register()
    yield


app = FastAPI(title="msft-agent-hackathon-2026", lifespan=lifespan)

# Vite dev servers for chat / review / admin UIs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(turn_router.router)
app.include_router(retrieval_router.router)
app.include_router(citations_router.router)
app.include_router(reviews_router.router)
app.include_router(hearout_router.router)
if schemas_router is not None:
    app.include_router(schemas_router.router)


@app.get("/healthz")
async def healthz() -> dict[str, bool]:
    return {"ok": True}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/version")
async def get_version() -> dict[str, str]:
    try:
        pkg_version = version("msft-agent-hackathon-2026")
    except PackageNotFoundError:
        pkg_version = "unknown"
    return {"version": pkg_version, "environment": settings.environment}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    reply = await run_hello_agent(req.message)
    return ChatResponse(reply=reply)
