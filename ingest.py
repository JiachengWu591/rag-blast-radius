"""Phase 0: index the fictional tenant corpus into a local chromadb collection.

Shared by every later phase — naive and isolated retrieval read from this
same collection; only how they query it differs.
"""

from pathlib import Path

import chromadb

CORPUS_DIR = Path(__file__).parent / "corpus"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "tenant_policies"

_SECTION_SLUGS = {
    "餐费标准": "meal",
    "住宿标准": "hotel",
    "审批流程": "approval",
    "发票要求": "invoice",
}


def _slugify_section(title: str, index: int) -> str:
    return _SECTION_SLUGS.get(title, f"section{index}")


def parse_policy_doc(path: Path) -> tuple[str, list[tuple[str, str]]]:
    """Parse a markdown policy doc into (company_name, [(chunk_slug, chunk_text), ...])."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    company_name = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else path.stem

    sections: list[tuple[str, list[str]]] = []
    for line in lines[1:]:
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)

    chunks: list[tuple[str, str]] = []
    for index, (title, body_lines) in enumerate(sections):
        body = "\n".join(body_lines).strip()
        if body:
            chunks.append((_slugify_section(title, index), body))
    return company_name, chunks


def discover_tenants(corpus_dir: Path) -> dict[str, Path]:
    """tenant_id -> its policy doc path, derived from the folder name (not doc content)."""
    tenants: dict[str, Path] = {}
    for tenant_dir in sorted(corpus_dir.iterdir()):
        if not tenant_dir.is_dir():
            continue
        docs = sorted(tenant_dir.glob("*.md"))
        if docs:
            tenants[tenant_dir.name] = docs[0]
    return tenants


def build_index() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(COLLECTION_NAME)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []

    for tenant_id, doc_path in discover_tenants(CORPUS_DIR).items():
        company_name, chunks = parse_policy_doc(doc_path)
        for chunk_slug, chunk_text in chunks:
            ids.append(f"{tenant_id}_{chunk_slug}")
            documents.append(chunk_text)
            metadatas.append(
                {
                    "tenant_id": tenant_id,
                    "company_name": company_name,
                    "doc_name": doc_path.name,
                    "section": chunk_slug,
                }
            )

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return collection


def main() -> None:
    collection = build_index()
    print(f"Indexed {collection.count()} chunks into '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
