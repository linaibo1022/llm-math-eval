"""答案判分模块：从模型输出里抽出答案，再判断它和标准答案是否等价。

核心难点：同一个答案有很多种写法。
    5/6  =  \\frac{5}{6}  =  0.8333...
    x=1 或 x=2  =  x=2, x=1
所以流程是：抽取 → 规范化 → 比较，而不是直接比字符串。
"""

from __future__ import annotations

import re
from fractions import Fraction

# \frac{1}{2}  ->  (1)/(2)
_FRAC = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
# 只由数字和四则运算组成的串
_NUM = re.compile(r"^[-+*/()0-9.]+$")
# 常见单位，比较前去掉
_UNITS = re.compile(r"(元|个|人|件|米|厘米|千克|克|小时|分钟|天)$")


def _extract_boxed(text: str) -> str | None:
    """取 \\boxed{...} 的内容。里面可能嵌套 \\frac{1}{2}，所以要配对括号。"""
    idx = text.find("\\boxed{")
    if idx == -1:
        return None
    start = idx + len("\\boxed{")
    depth = 1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i].strip()
    return None


def extract_answer(text: str) -> str:
    """从模型输出里取出最终答案。按优先级依次尝试。"""
    if not text:
        return ""

    # 1) LaTeX 的 \boxed{...}
    boxed = _extract_boxed(text)
    if boxed:
        return boxed

    # 2) "答案是 ..." / "答案：..."
    m = re.search(r"答案\s*[是为:：]\s*(.+)", text)
    if m:
        return m.group(1).strip().splitlines()[0].strip()

    # 3) 兜底：最后一行
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def normalize(s: str) -> str:
    """去掉空格、句号、货币符号，统一全角与多解分隔符。"""
    s = s.strip().lower()
    s = s.replace("＝", "=").replace("，", ",").replace("。", ".")
    s = s.replace("或", ",").replace("、", ",")
    s = re.sub(r"[\s$]", "", s)
    s = _UNITS.sub("", s)
    return s.rstrip(".")


def _to_fraction(s: str):
    """如果 s 是纯数字表达式，返回 Fraction；否则返回 None。"""
    s = _FRAC.sub(lambda m: f"({m.group(1)})/({m.group(2)})", s)
    s = s.replace("^", "**")
    if not _NUM.match(s):
        return None
    try:
        # 只允许数字和四则运算，禁用内置函数
        value = eval(s, {"__builtins__": {}}, {})  # noqa: S307
        return Fraction(value).limit_denominator(10**9)
    except Exception:
        return None


def _split_set(s: str):
    return {p for p in s.split(",") if p}


def is_correct(pred: str, gold: str, tol: float = 1e-9) -> bool:
    """判断预测答案是否与标准答案等价。"""
    p, g = normalize(pred), normalize(gold)
    if not p:
        return False
    if p == g:
        return True

    # 多解：按集合比较，顺序无关
    ps, gs = _split_set(p), _split_set(g)
    if len(gs) > 1 or len(ps) > 1:
        strip = lambda x: re.sub(r"^[a-z]=", "", x)
        if {strip(x) for x in ps} == {strip(x) for x in gs}:
            return True

    # 数值：转成分数后比较
    pf, gf = _to_fraction(p), _to_fraction(g)
    if pf is not None and gf is not None:
        return abs(float(pf) - float(gf)) <= tol

    return False
