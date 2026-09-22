"""Phase 3: a single entry point that runs one query end-to-end through
either version and logs the result. Phase 4's comparison script reuses this
same function for all five combinations instead of re-implementing dispatch.
"""

import chromadb

from baseline import answer as baseline_answer
from fixed import answer as fixed_answer
from ingest import build_index
from query_log import log_query
from retrieval import naive_search
from tenants import other_tenants_identifiers


def _naive_ignoring_tenant_filter(collection: chromadb.Collection, query: str, tenant_id: str, top_k: int = 5) -> list[dict]:
    """Stand-in for a broken isolated_search that forgot to apply the
    tenant filter -- same call shape, but silently falls back to a
    full-index search. Used only by the red-team drill below.
    """
    return naive_search(collection, query, top_k=top_k)


def run(version: str, tenant_id: str, query: str) -> dict:
    """Run one query through `version` ("baseline" | "fixed") and log it."""
    collection = build_index()

    if version == "baseline":
        text, chunks = baseline_answer(collection, query)
        validation_result = "not_applicable"
        reasoning, cited_chunk_ids = None, None
    elif version == "fixed":
        other_identifiers = other_tenants_identifiers(collection, tenant_id)
        result = fixed_answer(collection, query, tenant_id, other_identifiers)
        text, chunks = result.text, result.chunks
        validation_result = "pass" if result.validation_failure is None else f"blocked:{result.validation_failure}"
        reasoning, cited_chunk_ids = result.reasoning, result.cited_chunk_ids
    else:
        raise ValueError(f"unknown version: {version!r}")

    return log_query(
        version=version,
        tenant_id=tenant_id,
        query=query,
        chunks=chunks,
        validation_result=validation_result,
        answer_text=text,
        reasoning=reasoning,
        cited_chunk_ids=cited_chunk_ids,
    )


def run_redteam_drill(tenant_id: str, query: str, max_attempts: int = 3) -> dict:
    """模拟检索隔离失效:生成+校验仍走修复版真实流程,但检索换成
    `_naive_ignoring_tenant_filter`(忽略租户过滤),测试校验层能不能在检索
    防线失守时兜底拦截。

    真实调用模型,拦截与否取决于模型这次会不会引用了错误租户的 chunk,所以
    重试几次以展示到一次真正被拦截的结果;每次尝试都照常记日志,不伪造结果。
    """
    collection = build_index()
    other_identifiers = other_tenants_identifiers(collection, tenant_id)

    entry: dict | None = None
    for _ in range(max_attempts):
        result = fixed_answer(collection, query, tenant_id, other_identifiers, search=_naive_ignoring_tenant_filter)
        validation_result = "pass" if result.validation_failure is None else f"blocked:{result.validation_failure}"
        entry = log_query(
            version="fixed(模拟检索隔离失效)",
            tenant_id=tenant_id,
            query=query,
            chunks=result.chunks,
            validation_result=validation_result,
            answer_text=result.text,
            reasoning=result.reasoning,
            cited_chunk_ids=result.cited_chunk_ids,
        )
        if result.validation_failure is not None:
            return entry
    return entry
