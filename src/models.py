"""模型接口。

现在用三个"假模型"跑通流程，目的是验证判分和统计，不是验证模型能力。
接真实模型时，把 call_model() 换成一次 HTTP 请求即可（见文件末尾）。
"""

from __future__ import annotations


def oracle(p) -> str:
    """满分模型：直接输出标准答案。用来验证判分不会误杀。"""
    return f"答案是 {p['answer']}"


def careless(p) -> str:
    """粗心模型：第 1、3 题答错，其余答对。用来验证判分能抓错。"""
    wrong = {"m001": "0.8333", "m003": "4"}
    if p["id"] in wrong:
        return f"答案是 {wrong[p['id']]}"
    return f"答案是 {p['answer']}"


def latex_style(p) -> str:
    """会写 LaTeX 的模型：把 5/6 写成 \\frac{5}{6}，测试解析鲁棒性。"""
    ans = p["answer"]
    if ans == "5/6":
        return r"由通分得 \boxed{\frac{5}{6}}"
    if ans == "x=1 或 x=2":
        return r"所以 \boxed{x=1 或 x=2}"
    return f"答案是 {ans}"


MODELS = {
    "oracle": oracle,
    "careless": careless,
    "latex_style": latex_style,
}


# ---- 接真实模型时参考这段 ----
# import os, requests
#
# def call_model(p):
#     resp = requests.post(
#         "https://api.deepseek.com/chat/completions",
#         headers={"Authorization": f"Bearer {os.environ['API_KEY']}"},
#         json={
#             "model": "deepseek-chat",
#             "messages": [{"role": "user", "content": p["question"]}],
#             "temperature": 0,
#         },
#         timeout=60,
#     )
#     return resp.json()["choices"][0]["message"]["content"]
