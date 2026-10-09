import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from allocation import SERVICE_PROVIDERS, hit_providers, judge  # noqa: E402

UID = "a1b2c3d4e5f6a7b8c9d0e1f2"


def acc(**kw):
    base = dict(uid=UID, name="t", sales="", sales_dept="", op="", op_dept="",
                agents=[], spend_120d=False, spend_180d=False)
    base.update(kw)
    return base


# ---------- 线索线 ----------
def test_lead_ok():
    assert judge(acc(sales="甲", sales_dept="线索一组", op="乙", op_dept="线索二组")).decision == "是"


def test_lead_own_provider_blocked():
    r = judge(acc(sales="甲", sales_dept="线索一组", op="乙", op_dept="线索二组", agents=["服务商A"]))
    assert r.decision == "否" and "服务商A" in r.reason


def test_lead_external_agent_not_blocked():
    assert judge(acc(op="乙", op_dept="线索二组", agents=["外部代理X"])).decision == "是"


def test_lead_ka_blocked():
    assert judge(acc(sales="甲", sales_dept="行业KA部", op="乙", op_dept="线索二组")).reason == "KA 客户"


def test_lead_sales_only_blocked():
    assert judge(acc(sales="甲", sales_dept="线索一组")).reason == "仅挂接销售"


def test_lead_op_in_virtual_pool_counts_as_sales_only():
    assert judge(acc(sales="甲", sales_dept="线索一组", op="丙", op_dept="线索虚拟池")).decision == "否"


# ---------- 消费品线 ----------
def test_consumer_pure_new_blocked():
    r = judge(acc(sales_dept="消费品一组"))
    assert r.decision == "否" and "纯新客" in r.reason


def test_consumer_has_spend_ok():
    assert judge(acc(sales_dept="消费品一组", spend_180d=True)).decision == "是"


def test_consumer_virtual_pool_ok_regardless_of_spend():
    # 回归：运营挂在虚拟池时不能被误判为纯新客
    assert judge(acc(op="丁", op_dept="消费品虚拟池")).decision == "是"


def test_consumer_own_provider_blocked():
    assert judge(acc(op="丁", op_dept="消费品二组", agents=["服务商B"], spend_120d=True)).decision == "否"


# ---------- 边界 ----------
def test_empty_dept_needs_manual():
    r = judge(acc())
    assert r.decision == "" and "人工" in r.reason


def test_cross_line_follows_op():
    assert judge(acc(sales="甲", sales_dept="消费品一组", op="乙", op_dept="线索二组")).line == "线索"


def test_invalid_uid():
    assert "UID" in judge(acc(uid="12345678")).reason


# ---------- 名单回归：用「系统真实返回名称」做正反两向测试 ----------
SYSTEM_RETURNED_INSIDE = [f"服务商{c}" for c in "ABCDEFGHIJKL"]          # 实际项目中来自 CRM 返回
SYSTEM_RETURNED_OUTSIDE = ["外部代理X", "外部代理Y", "服务商甲", "服务商 A"]  # 名单外 / 近似名


def test_provider_list_regression():
    assert len(SERVICE_PROVIDERS) == 12
    assert hit_providers(SYSTEM_RETURNED_INSIDE) == SYSTEM_RETURNED_INSIDE   # 正向：全命中
    assert hit_providers(SYSTEM_RETURNED_OUTSIDE) == []                       # 反向：全排除
