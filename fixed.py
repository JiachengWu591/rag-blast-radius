"""Phase 2: structurally isolated fixed version.

Retrieval carries the tenant constraint inside the query itself (see
retrieval.isolated_search) -- the candidate pool outside the tenant's own
chunks never exists; it is not filtered out afterwards. Generation uses the
3.2 schema via a forced tool call (3.3), and every answer passes through the
3.4 three-layer validation before being returned.
"""

import json
import os
from collections.abc import Callable

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from ingest import build_index
from retrieval import isolated_search
from tenants import other_tenants_identifiers
from validate import validate

load_dotenv()

_client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
_MODEL = "deepseek-chat"

FAIL_CLOSED_MESSAGE = "没有找到相关信息"

_TOOL_NAME = "submit_answer"

_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": _TOOL_NAME,
        "description": "提交本次回答",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": (
                        "说明打算依据哪些检索到的片段来回答、为什么选这些片段、如果信息不足该怎么说明。"
                        "仅供日志/调试,不直接展示给用户。"
                    ),
                },
                "answer": {
                    "type": "string",
                    "description": "给用户看的最终回答文本。",
                },
                "cited_chunk_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "实际支撑这个回答的 chunk_id,必须是这一轮检索真实返回过的 id,不能编造。",
                },
            },
            "required": ["reasoning", "answer", "cited_chunk_ids"],
        },
    },
}

_PROMPT_TEMPLATE = """你是内部知识助手。请只依据下面提供的资料回答用户的问题,并调用工具提交结果。
如果资料里没有足够信息回答,在 answer 里如实说明,cited_chunk_ids 留空。

资料:
{context}

用户问题:{query}"""


def _build_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{chunk['id']}] {chunk['document']}" for chunk in chunks)


def _validate_schema(parsed: object) -> None:
    if not isinstance(parsed, dict):
        raise ValueError("参数不是一个 JSON 对象")
    for key in ("reasoning", "answer", "cited_chunk_ids"):
        if key not in parsed:
            raise ValueError(f"缺少必填字段: {key}")
    if not isinstance(parsed["reasoning"], str) or not isinstance(parsed["answer"], str):
        raise ValueError("reasoning/answer 必须是字符串")
    if not isinstance(parsed["cited_chunk_ids"], list) or not all(
        isinstance(item, str) for item in parsed["cited_chunk_ids"]
    ):
        raise ValueError("cited_chunk_ids 必须是字符串数组")


def _call_model(prompt: str) -> dict | None:
    """3.3: 强制工具调用拿结构化输出;失败把错误信息喂回去重试一次,仍失败返回 None。"""
    current_prompt = prompt
    for attempt in range(2):
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": current_prompt}],
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "function", "function": {"name": _TOOL_NAME}},
        )
        tool_calls = response.choices[0].message.tool_calls
        try:
            if not tool_calls:
                raise ValueError("模型没有返回工具调用")
            parsed = json.loads(tool_calls[0].function.arguments)
            _validate_schema(parsed)
            return parsed
        except (ValueError, json.JSONDecodeError) as exc:
            if attempt == 0:
                current_prompt = (
                    f"{prompt}\n\n[上一次调用失败: {exc}。请重新正确调用 {_TOOL_NAME} 工具,严格按 schema 输出。]"
                )
                continue
            return None
    return None


def answer(
    collection: chromadb.Collection,
    query: str,
    tenant_id: str,
    other_identifiers: dict[str, list[str]],
    top_k: int = 5,
    search: Callable[..., list[dict]] = isolated_search,
) -> tuple[str, list[dict], str | None]:
    """Return (final_answer_text, retrieved_chunks, validation_failure).

    `search` defaults to isolated_search (the real fixed-version retrieval).
    Phase 3's red-team drill passes in a stand-in that ignores the tenant
    filter, to test whether validation still catches the leak when
    retrieval isolation itself has failed -- generation and validation
    below are otherwise untouched.
    """
    chunks = search(collection, query, tenant_id, top_k=top_k)
    if not chunks:
        # 检索结果为空时直接短路返回 fail-closed 文案,不调用模型——不给它任何
        # "自己想办法回答"的机会,也就没有"放宽过滤去补答案"的空间。
        return FAIL_CLOSED_MESSAGE, chunks, "empty_retrieval"

    prompt = _PROMPT_TEMPLATE.format(context=_build_context(chunks), query=query)
    parsed = _call_model(prompt)
    if parsed is None:
        return FAIL_CLOSED_MESSAGE, chunks, "schema_generation_failed"

    failure = validate(
        cited_chunk_ids=parsed["cited_chunk_ids"],
        retrieved_chunks=chunks,
        answer_text=parsed["answer"],
        tenant_id=tenant_id,
        other_identifiers=other_identifiers,
    )
    if failure is not None:
        return FAIL_CLOSED_MESSAGE, chunks, failure

    return parsed["answer"], chunks, None


def main() -> None:
    collection = build_index()
    tenant_id = "tenant_a"
    other_identifiers = other_tenants_identifiers(collection, tenant_id)
    query = "我们公司出差,一天餐费最多能报多少?住宿呢?"

    text, chunks, failure = answer(collection, query, tenant_id, other_identifiers)

    print(f"Query: {query} (tenant={tenant_id})\n")
    print("Retrieved chunks:")
    for chunk in chunks:
        print(f"  {chunk['id']:<20} tenant_id={chunk['tenant_id']}")
    print(f"\nValidation failure: {failure}")
    print(f"Answer:\n{text}")


if __name__ == "__main__":
    main()
