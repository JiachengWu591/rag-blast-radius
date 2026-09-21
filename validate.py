"""3.4 三层校验规则.

由调用方(demo 脚本 / 运行时)执行,不是生成 Agent 自己负责的——模型的输出必须
经过这三层确定性检查才能被放行,检查逻辑完全不依赖模型是否"讲道理"。
"""


def check_existence(cited_chunk_ids: list[str], retrieved_chunks: list[dict]) -> bool:
    """引用的每个 id 必须真实出现在这一轮检索结果里,防止编造 id。"""
    retrieved_ids = {chunk["id"] for chunk in retrieved_chunks}
    return all(chunk_id in retrieved_ids for chunk_id in cited_chunk_ids)


def check_ownership(cited_chunk_ids: list[str], retrieved_chunks: list[dict], tenant_id: str) -> bool:
    """引用的每个 id 对应 chunk 的 tenant_id 必须等于发起查询的租户。"""
    retrieved_by_id = {chunk["id"]: chunk for chunk in retrieved_chunks}
    return all(
        chunk_id in retrieved_by_id and retrieved_by_id[chunk_id]["tenant_id"] == tenant_id
        for chunk_id in cited_chunk_ids
    )


def check_leak_scan(answer_text: str, other_identifiers: dict[str, list[str]]) -> bool:
    """兜底扫描: answer 文本本身不能包含其它租户的已知唯一标识符,不依赖 cited_chunk_ids 是否准确。"""
    return not any(number in answer_text for numbers in other_identifiers.values() for number in numbers)


def validate(
    cited_chunk_ids: list[str],
    retrieved_chunks: list[dict],
    answer_text: str,
    tenant_id: str,
    other_identifiers: dict[str, list[str]],
) -> str | None:
    """依次跑三层校验,返回第一个失败的规则名;全部通过则返回 None。

    先查存在性再查归属,这样一个编造的 id 会被准确报告为 existence 失败,
    而不是被误判成 ownership 失败。
    """
    if not check_existence(cited_chunk_ids, retrieved_chunks):
        return "existence"
    if not check_ownership(cited_chunk_ids, retrieved_chunks, tenant_id):
        return "ownership"
    if not check_leak_scan(answer_text, other_identifiers):
        return "leak_scan"
    return None
