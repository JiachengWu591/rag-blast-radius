"""Phase 4 acceptance check.

Runs the one-command comparison and asserts the report is actually there and
actually says the right thing: baseline leaks on both attack scenarios,
fixed leaks on none of its three runs (two attack scenarios + control), and
every combination the report claims to cover is really in it.
"""

from compare import COMBOS, REPORT_PATH, build_report, run_all
from ingest import build_index
from tenants import find_leaks, known_identifiers, other_tenants_identifiers, tenant_company_names

ASKING_TENANT = "tenant_a"


def main() -> None:
    collection = build_index()
    own_identifiers = known_identifiers(collection, ASKING_TENANT)
    other_identifiers = other_tenants_identifiers(collection, ASKING_TENANT)
    company_names = tenant_company_names(collection)

    results = run_all()
    report = build_report(results, own_identifiers, other_identifiers, company_names)
    REPORT_PATH.write_text(report, encoding="utf-8")

    failures: list[str] = []

    if len(results) != len(COMBOS):
        failures.append(f"跑出来的组合数量 ({len(results)}) 跟预期 ({len(COMBOS)}) 不一致")

    for entry in results:
        leaks = find_leaks(entry["answer"], other_identifiers)
        if entry["version"] == "baseline":
            if not leaks:
                failures.append(f"baseline / {entry['scenario_label']}: 没有复现泄露")
        else:
            if leaks:
                failures.append(f"fixed / {entry['scenario_label']}: 泄露了其它租户的数字 ({leaks})")
            if not entry["validation_result"] == "pass":
                failures.append(
                    f"fixed / {entry['scenario_label']}: 校验没有通过 ({entry['validation_result']}),"
                    "本该在正常场景下顺利放行"
                )

    if not REPORT_PATH.exists() or not REPORT_PATH.read_text(encoding="utf-8").strip():
        failures.append(f"报告文件不存在或为空: {REPORT_PATH}")
    else:
        report_text = REPORT_PATH.read_text(encoding="utf-8")
        for _, label, _ in COMBOS:
            if label not in report_text:
                failures.append(f"报告里没有找到场景标签: {label}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)

    print(f"PASS —— 5 种组合全部符合预期,报告已写入 {REPORT_PATH}。")


if __name__ == "__main__":
    main()
