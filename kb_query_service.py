"""Shared utilities for issuing knowledge base queries.

This module centralizes the KnowledgeBaseRetrievalClient setup so both the
console app and the web app can reuse the same session-oriented client and
response-shaping logic.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    SearchIndexKnowledgeSourceParams,
)

load_dotenv()


class KBConfigurationError(RuntimeError):
    """Raised when mandatory configuration is missing."""


@lru_cache(maxsize=1)
def _load_settings() -> Dict[str, Any]:
    search_url = os.getenv("search_url")
    api_key = os.getenv("search_api_key")
    if not search_url or not api_key:
        raise KBConfigurationError(
            "Both 'search_url' and 'search_api_key' must be configured in the environment."
        )

    return {
        "search_url": search_url,
        "api_key": api_key,
        "knowledge_base_name": os.getenv("knowledge_base_name", "contoso-multi-index-kb"),
        "index_insurance": os.getenv("index_insurance", "contoso-insurance-faq-index"),
        "index_retail": os.getenv("index_retail", "contoso-retail-index"),
        "index_gaming": os.getenv("index_gaming", "contoso-gaming-index"),
    }


@lru_cache(maxsize=1)
def _get_kb_client() -> KnowledgeBaseRetrievalClient:
    settings = _load_settings()
    return KnowledgeBaseRetrievalClient(
        endpoint=settings["search_url"],
        knowledge_base_name=settings["knowledge_base_name"],
        credential=AzureKeyCredential(settings["api_key"]),
    )


def _build_request(question: str) -> KnowledgeBaseRetrievalRequest:
    settings = _load_settings()
    source_params = [
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=settings["index_insurance"],
            include_references=True,
            include_reference_source_data=True,
            always_query_source=False,
        ),
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=settings["index_retail"],
            include_references=True,
            include_reference_source_data=True,
            always_query_source=False,
        ),
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=settings["index_gaming"],
            include_references=True,
            include_reference_source_data=True,
            always_query_source=False,
        ),
    ]

    return KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text=question.strip())],
            )
        ],
        knowledge_source_params=source_params,
        include_activity=True,
    )


def _extract_answer_texts(result: Any) -> List[str]:
    texts: List[str] = []
    if getattr(result, "response", None):
        for response_item in result.response:
            if getattr(response_item, "content", None):
                parts: List[str] = []
                for content_item in response_item.content:
                    text_value = getattr(content_item, "text", None)
                    if text_value:
                        parts.append(text_value.strip())
                if parts:
                    texts.append("\n\n".join(parts))
    return texts


def _clean_content(content: Optional[str]) -> Optional[str]:
    if not content:
        return None
    return content.replace("\r\n", "\n").replace("\t", "  ").strip()


def _format_reference(idx: int, reference: Any) -> Dict[str, Any]:
    source_type = getattr(reference, "type", "unknown")
    formatted: Dict[str, Any] = {
        "id": idx,
        "type": source_type,
        "title": None,
        "url": None,
        "citationText": None,
        "note": None,
        "document": None,
        "relevanceScore": getattr(reference, "reranker_score", None),
    }

    source_data = getattr(reference, "source_data", None)
    additional_props = getattr(reference, "additional_properties", None)

    if source_type == "web":
        if isinstance(source_data, dict):
            formatted["title"] = source_data.get("name", "Web Source")
            formatted["url"] = source_data.get("url")
            formatted["note"] = (
                source_data.get("snippet")
                or "Web Knowledge Source references omit extractive snippets by design."
            )
        else:
            formatted["note"] = "Web Knowledge Source references omit extractive snippets by design."
    elif source_type == "searchIndex":
        if isinstance(additional_props, dict):
            formatted["document"] = additional_props.get("title")
            if not formatted["title"]:
                formatted["title"] = additional_props.get("title")
        if isinstance(source_data, dict):
            formatted["title"] = formatted["title"] or source_data.get("title")
            formatted["url"] = source_data.get("url")
            formatted["citationText"] = _clean_content(source_data.get("content"))
    else:
        if isinstance(source_data, dict):
            formatted["note"] = str(source_data)

    return formatted


def _format_references(result: Any) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
    references = getattr(result, "references", None)
    if not references:
        return formatted

    for idx, reference in enumerate(references):
        formatted.append(_format_reference(idx, reference))
    return formatted


def execute_kb_query(question: str) -> Dict[str, Any]:
    """Execute a single KB query and return structured data for UI layers."""

    if not question or not question.strip():
        raise ValueError("Question text is required.")

    request_timing_start = time.perf_counter()
    request = _build_request(question)
    request_prep_time = time.perf_counter() - request_timing_start

    retrieval_start = time.perf_counter()
    result = _get_kb_client().retrieve(request)
    retrieval_time = time.perf_counter() - retrieval_start

    processing_start = time.perf_counter()
    answers = _extract_answer_texts(result)
    citations = _format_references(result)
    processing_time = time.perf_counter() - processing_start

    total_time = request_prep_time + retrieval_time + processing_time
    settings = _load_settings()

    return {
        "question": question.strip(),
        "answers": answers,
        "citations": citations,
        "timing": {
            "total": total_time,
            "requestPreparation": request_prep_time,
            "kbRetrieval": retrieval_time,
            "responseProcessing": processing_time,
        },
        "metadata": {
            "knowledgeBaseName": settings["knowledge_base_name"],
            "searchEndpoint": settings["search_url"],
        },
        "activity": getattr(result, "activity", None),
    }


def get_kb_configuration() -> Dict[str, Any]:
    """Expose key configuration values for UI layers."""

    settings = _load_settings()
    return {
        "searchEndpoint": settings["search_url"],
        "knowledgeBaseName": settings["knowledge_base_name"],
        "indexes": [
            settings["index_insurance"],
            settings["index_retail"],
            settings["index_gaming"],
        ],
    }
