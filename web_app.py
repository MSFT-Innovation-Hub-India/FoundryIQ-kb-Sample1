"""FastAPI web application for interactive knowledge base queries."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from kb_query_service import KBConfigurationError, execute_kb_query, get_kb_configuration

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Contoso Knowledge Base", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class QueryPayload(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    retrieval_reasoning_effort: Optional[str] = Field(
        default=None,
        alias="retrievalReasoningEffort",
        description="Optional override for retrieval reasoning effort",
    )
    output_mode: Optional[str] = Field(
        default=None,
        alias="knowledgeRetrievalOutputMode",
        description="Optional override for knowledge retrieval output mode",
    )

    class Config:
        allow_population_by_field_name = True


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    config = get_kb_configuration()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": config,
        },
    )


@app.post("/api/query")
async def query_kb(payload: QueryPayload):
    try:
        result = execute_kb_query(
            payload.question,
            retrieval_reasoning_effort=payload.retrieval_reasoning_effort,
            output_mode=payload.output_mode,
        )
        return result
    except KBConfigurationError as exc:  # pragma: no cover - configuration guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - generic fallback
        raise HTTPException(status_code=500, detail="Unable to process the query.") from exc


@app.get("/health")
async def health_check():
    """Simple health endpoint for readiness probes."""

    return {"status": "ok"}
