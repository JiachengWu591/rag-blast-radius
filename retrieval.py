"""Retrieval query construction.

Naive (Phase 1) and isolated (Phase 2) search both read the same chromadb
collection built in Phase 0 — the only difference is how the query itself is
constructed, per the project's core design point (see PROJECT_SPEC.md §2).
"""

import chromadb


def naive_search(collection: chromadb.Collection, query: str, top_k: int = 5) -> list[dict]:
    """Phase 1 baseline: search the whole index, with no tenant constraint."""
    result = collection.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas"])
    return [
        {
            "id": chunk_id,
            "document": document,
            "tenant_id": metadata["tenant_id"],
            "company_name": metadata["company_name"],
            "metadata": metadata,
        }
        for chunk_id, document, metadata in zip(result["ids"][0], result["documents"][0], result["metadatas"][0])
    ]
