"""自助户分配判定模块（脱敏版）。

设计原则：
- 独立模块，只读取挂接查询结果，不修改任何原有判定；
- 能确定的给出「是 / 否」，确定不了的输出「空」并写明原因，交给人工判断。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 自家服务商名单（脱敏为 服务商A ~ 服务商L）。增删只需修改这里。
SERVICE_PROVIDERS: set[str] = {f"服务商{c}" for c in "ABCDEFGHIJKL"}

LEAD_DEPT_KEYWORD = "线索"        # 线索线部门关键词
CONSUMER_DEPT_KEYWORD = "消费品"  # 消费品线部门关键词
KA_DEPT_KEYWORD = "行业"          # KA 部门关键词
VIRTUAL_POOL_KEYWORD = "虚拟池"   # 虚拟挂接池（不算真人挂接，也不算 KA）

UID_PATTERN = re.compile(r"^[0-9a-f]{24}$")


@dataclass
class Result:
    line: str      # 线索 / 消费品 / ""
    decision: str  # 是 / 否 / ""
    reason: str = ""


def is_valid_uid(uid: str) -> bool:
    return bool(UID_PATTERN.match(uid or ""))


def _is_real(person: str, dept: str) -> bool:
    """有人名，且不在虚拟挂接池里，才算真人挂接。"""
    return bool(person) and VIRTUAL_POOL_KEYWORD not in (dept or "")


def resolve_line(acc: dict) -> str:
    """销售和运营不在同一条线时，以运营部门为准。"""
    for dept in (acc.get("op_dept", ""), acc.get("sales_dept", "")):
        if LEAD_DEPT_KEYWORD in dept:
            return "线索"
        if CONSUMER_DEPT_KEYWORD in dept:
            return "消费品"
    return ""


def hit_providers(agents: list[str]) -> list[str]:
    return [a for a in agents if a in SERVICE_PROVIDERS]


def judge(acc: dict) -> Result:
    if not is_valid_uid(acc.get("uid", "")):
        return Result("", "", "UID 格式异常，应为 24 位十六进制")

    line = resolve_line(acc)
    if not line:
        return Result("", "", "部门归属为空，需人工确认")

    hits = hit_providers(acc.get("agents", []))
    if hits:
        return Result(line, "否", f"已挂接自家服务商：{'、'.join(hits)}")

    sales_real = _is_real(acc.get("sales", ""), acc.get("sales_dept", ""))
    op_real = _is_real(acc.get("op", ""), acc.get("op_dept", ""))

    if line == "线索":
        sd = acc.get("sales_dept", "")
        if KA_DEPT_KEYWORD in sd and VIRTUAL_POOL_KEYWORD not in sd:
            return Result(line, "否", "KA 客户")
        if sales_real and not op_real:
            return Result(line, "否", "仅挂接销售")
        return Result(line, "是")

    # 消费品线
    if acc.get("op") and VIRTUAL_POOL_KEYWORD in acc.get("op_dept", ""):
        return Result(line, "是")
    if not sales_real and not op_real and not acc.get("spend_120d") and not acc.get("spend_180d"):
        return Result(line, "否", "纯新客（无挂接且 120/180 天无消耗）")
    return Result(line, "是")
