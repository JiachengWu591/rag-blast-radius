"""Phase 1: naive baseline.

Retrieval has no tenant constraint (see retrieval.naive_search); generation
just pastes the retrieved chunks into a prompt and returns plain text — no
3.2 structured-output schema, because a baseline should stay naive. Note
that answer() never takes a tenant_id: the naive path is structurally
incapable of considering who is asking, which is exactly the gap Phase 2
closes.
"""

import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from ingest import build_index
from retrieval import naive_search

load_dotenv()

_client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
_MODEL = "deepseek-chat"

_PROMPT_TEMPLATE = """你是内部知识助手。请只依据下面提供的资料回答用户的问题。

资料:
{context}

用户问题:{query}"""


def _build_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{chunk['company_name']} | {chunk['id']}] {chunk['document']}" for chunk in chunks)


def answer(collection: chromadb.Collection, query: str, top_k: int = 5) -> tuple[str, list[dict]]:
    """Return (answer_text, retrieved_chunks) for a naive baseline query."""
    chunks = naive_search(collection, query, top_k=top_k)
    prompt = _PROMPT_TEMPLATE.format(context=_build_context(chunks), query=query)
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content, chunks


def main() -> None:
    collection = build_index()
    query = "我们公司出差,一天餐费最多能报多少?住宿呢?"
    text, chunks = answer(collection, query)

    print(f"Query: {query}\n")
    print("Retrieved chunks:")
    for chunk in chunks:
        print(f"  {chunk['id']:<20} tenant_id={chunk['tenant_id']} company={chunk['company_name']}")
    print(f"\nAnswer:\n{text}")


if __name__ == "__main__":
    main()
