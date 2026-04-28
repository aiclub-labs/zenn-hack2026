from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.agents.hello_agent import run_hello_agent
from app.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.applicationinsights_connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string
        )
    yield


app = FastAPI(title="msft-agent-hackathon-2026", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    reply = await run_hello_agent(req.message)
    return ChatResponse(reply=reply)
