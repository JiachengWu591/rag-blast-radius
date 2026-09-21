"""Phase 3 observability.

Append one structured JSON-Lines record per query, and render the log back
to the terminal in a human-readable form.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "logs" / "queries.jsonl"


def log_query(
    version: str,
    tenant_id: str,
    query: str,
    chunks: list[dict],
    validation_result: str,
    answer_text: str,
) -> dict:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "tenant_id": tenant_id,
        "query": query,
        "retrieved_chunks": [{"chunk_id": chunk["id"], "tenant_id": chunk["tenant_id"]} for chunk in chunks],
        "validation_result": validation_result,
        "answer": answer_text,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def render_entry(entry: dict) -> str:
    lines = [
        f"[{entry['timestamp']}] version={entry['version']} tenant={entry['tenant_id']}",
        f"  问题: {entry['query']}",
        "  检索到的 chunk:",
    ]
    if entry["retrieved_chunks"]:
        lines.extend(
            f"    - {chunk['chunk_id']} (tenant_id={chunk['tenant_id']})" for chunk in entry["retrieved_chunks"]
        )
    else:
        lines.append("    (无)")
    lines.append(f"  校验结果: {entry['validation_result']}")
    lines.append(f"  回答: {entry['answer']}")
    return "\n".join(lines)


def read_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8") as log_file:
        return [json.loads(line) for line in log_file if line.strip()]


def main() -> None:
    entries = read_entries()
    print(f"共 {len(entries)} 条日志记录,来自 {LOG_PATH}\n")
    for entry in entries:
        print(render_entry(entry))
        print()


if __name__ == "__main__":
    main()
