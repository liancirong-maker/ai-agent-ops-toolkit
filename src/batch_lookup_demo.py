"""批量挂接查询 + 分配判定示例。

用法：
    python src/batch_lookup_demo.py --input sample_data/demo_accounts.csv          # 只查挂接
    python src/batch_lookup_demo.py --input sample_data/demo_accounts.csv --alloc  # 加分配判定
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from allocation import judge, resolve_line  # noqa: E402
from mock_crm import load_accounts  # noqa: E402

BASE_COLS = ["UID", "名称", "部门归属", "销售", "销售部门", "运营", "运营部门", "代理商"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="output/result.csv")
    ap.add_argument("--alloc", action="store_true", help="开启分配判定（不开时输出与原版一致）")
    args = ap.parse_args()

    rows = []
    for acc in load_accounts(args.input):
        row = [acc["uid"], acc["name"], resolve_line(acc), acc["sales"], acc["sales_dept"],
               acc["op"], acc["op_dept"], "|".join(acc["agents"])]
        if args.alloc:
            r = judge(acc)
            row += [r.decision, r.reason]
        rows.append(row)

    cols = BASE_COLS + (["分配结果", "说明"] if args.alloc else [])
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)

    for r in rows:
        tail = f"  {r[8] or '—'}  {r[9]}" if args.alloc else ""
        print(f"{r[0]}  {r[1]:<10}  {r[2] or '—'}{tail}")
    if args.alloc:
        stat = {k: sum(1 for r in rows if r[8] == k) for k in ("是", "否", "")}
        print(f"\n共 {len(rows)} 个：可分配 {stat['是']} / 不可分配 {stat['否']} / 待确认 {stat['']}")
    print(f"结果已导出：{out}")


if __name__ == "__main__":
    main()
