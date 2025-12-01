"""Remove a knowledge source from an existing knowledge base.

This utility removes a knowledge source reference from a knowledge base so
that future retrieval requests no longer route to that source.

Usage (from repo root):
    python ops/delete_knowledge_source.py --knowledge-source-name nykaa-financials-indexer

The script automatically reads the Search endpoint and admin key from the
project's .env file, ensuring it uses the same configuration as the other ops
utilities.
"""

import argparse
import os
import sys
from typing import List, Tuple, Any

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-source-name",
        "-s",
        required=True,
        help="Name of the knowledge source to remove (must match the KB reference)",
    )
    parser.add_argument(
        "--knowledge-base-name",
        "-k",
        default=os.getenv("knowledge_base_name", "contoso-multi-index-kb"),
        help="Knowledge base name (defaults to knowledge_base_name from .env)",
    )
    return parser.parse_args()


def _load_search_settings() -> Tuple[str, str]:
    search_url = os.getenv("search_url")
    search_key = os.getenv("search_api_key")

    if not search_url:
        raise ValueError("search_url is required; set it in your .env file.")
    if not search_key:
        raise ValueError("search_api_key is required; set it in your .env file.")

    return search_url, search_key


def _remove_source(
    client: SearchIndexClient,
    kb_name: str,
    source_name: str,
) -> None:
    knowledge_base = client.get_knowledge_base(kb_name)
    if not knowledge_base:
        raise RuntimeError(f"Knowledge base '{kb_name}' was not found.")

    sources: List[Any] = list(knowledge_base.knowledge_sources or [])
    remaining = [source for source in sources if getattr(source, "name", None) != source_name]

    if len(remaining) == len(sources):
        print(f"Knowledge source '{source_name}' was not referenced by '{kb_name}'.")
        return

    knowledge_base.knowledge_sources = remaining
    client.create_or_update_knowledge_base(knowledge_base)
    print(
        f"Knowledge source '{source_name}' removed from knowledge base '{kb_name}'."
    )


def main() -> None:
    load_dotenv()
    args = _parse_args()
    search_url, search_key = _load_search_settings()

    client = SearchIndexClient(
        endpoint=search_url,
        credential=AzureKeyCredential(search_key),
    )

    try:
        _remove_source(client, args.knowledge_base_name, args.knowledge_source_name)
    except Exception as exc:  # pragma: no cover - tooling convenience
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
