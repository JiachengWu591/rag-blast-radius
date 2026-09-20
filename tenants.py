"""Shared tenant helpers.

Derives each tenant's "known unique identifiers" (its reimbursement figures)
straight from its own indexed meal/hotel chunks, rather than maintaining a
second hardcoded copy of numbers that already live in the corpus. Phase 1's
leak detection and Phase 2's string-scan guardrail both read this same list.
"""

import re

import chromadb

_IDENTIFIER_SECTIONS = ("meal", "hotel")
_AMOUNT_PATTERN = re.compile(r"(\d+)\s*元")


def all_tenant_ids(collection: chromadb.Collection) -> list[str]:
    result = collection.get(include=["metadatas"])
    return sorted({metadata["tenant_id"] for metadata in result["metadatas"]})


def known_identifiers(collection: chromadb.Collection, tenant_id: str) -> list[str]:
    """A tenant's reimbursement figures, extracted from its own meal/hotel chunks."""
    ids = [f"{tenant_id}_{section}" for section in _IDENTIFIER_SECTIONS]
    result = collection.get(ids=ids, include=["documents"])
    identifiers: list[str] = []
    for document in result["documents"]:
        match = _AMOUNT_PATTERN.search(document)
        if match:
            identifiers.append(match.group(1))
    return identifiers


def other_tenants_identifiers(collection: chromadb.Collection, tenant_id: str) -> dict[str, list[str]]:
    """tenant_id -> its identifiers, for every tenant except the given one."""
    return {
        other_id: known_identifiers(collection, other_id)
        for other_id in all_tenant_ids(collection)
        if other_id != tenant_id
    }
