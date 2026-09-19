"""Phase 0 acceptance check.

Indexes the full corpus, prints every chunk's tenant_id, then asserts the
basic invariants a later phase will rely on. Exits non-zero on FAIL.
"""

from ingest import CHROMA_DIR, COLLECTION_NAME, CORPUS_DIR, build_index, discover_tenants


def main() -> None:
    expected_tenants = set(discover_tenants(CORPUS_DIR))
    collection = build_index()

    result = collection.get(include=["metadatas"])
    ids: list[str] = result["ids"]
    metadatas: list[dict[str, str]] = result["metadatas"]

    print(f"Collection '{COLLECTION_NAME}' at {CHROMA_DIR}: {len(ids)} chunks\n")

    failures: list[str] = []
    per_tenant_count: dict[str, int] = {}

    for chunk_id, metadata in sorted(zip(ids, metadatas), key=lambda pair: pair[0]):
        tenant_id = metadata.get("tenant_id")
        print(f"  {chunk_id:<20} tenant_id={tenant_id}")
        if tenant_id not in expected_tenants:
            failures.append(f"chunk {chunk_id!r} has unexpected tenant_id={tenant_id!r}")
            continue
        per_tenant_count[tenant_id] = per_tenant_count.get(tenant_id, 0) + 1

    print()
    for tenant_id in sorted(expected_tenants):
        count = per_tenant_count.get(tenant_id, 0)
        print(f"  {tenant_id}: {count} chunks")
        if count == 0:
            failures.append(f"tenant {tenant_id!r} has zero indexed chunks")

    if len(ids) != len(set(ids)):
        failures.append("duplicate chunk ids found in the collection")

    print()
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)

    print("PASS")


if __name__ == "__main__":
    main()
