"""Mock 数据源：模拟 CRM 挂接查询接口返回。

真实环境中这里是对 CRM API 的调用；本仓库用本地 CSV 代替，所有数据均为虚构。
"""
import csv
from pathlib import Path


def _to_bool(v: str) -> bool:
    return str(v).strip() in {"是", "1", "true", "True", "Y", "y"}


def load_accounts(csv_path: str) -> list[dict]:
    rows = []
    with open(Path(csv_path), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "uid": r["uid"].strip(),
                "name": r["name"].strip(),
                "sales": r.get("sales", "").strip(),
                "sales_dept": r.get("sales_dept", "").strip(),
                "op": r.get("op", "").strip(),
                "op_dept": r.get("op_dept", "").strip(),
                "agents": [a.strip() for a in r.get("agents", "").split("|") if a.strip()],
                "spend_120d": _to_bool(r.get("spend_120d", "")),
                "spend_180d": _to_bool(r.get("spend_180d", "")),
            })
    return rows
