"""跑评测：加载题目 → 让每个模型作答 → 判分 → 出表。

用法：
    python run_eval.py

说明：控制台输出用英文标签，避免 Windows 终端的中文乱码；
中文内容保存在 README、report.md 和数据文件里。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from judge import extract_answer, is_correct  # noqa: E402
from models import MODELS  # noqa: E402

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "problems.jsonl"


def load_problems(path: Path) -> list[dict]:
    problems = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))
    return problems


def evaluate(name: str, fn, problems: list[dict]) -> dict:
    rows = []
    for p in problems:
        raw = fn(p)
        pred = extract_answer(raw)
        ok = is_correct(pred, p["answer"])
        rows.append({"id": p["id"], "pred": pred, "gold": p["answer"], "ok": ok})
    acc = sum(r["ok"] for r in rows) / len(rows) if rows else 0.0
    return {"model": name, "acc": acc, "rows": rows}


def print_table(results: list[dict]) -> None:
    print(f"{'model':<14}{'acc':>8}{'ok':>6}{'total':>7}")
    print("-" * 35)
    for r in results:
        n_ok = sum(x["ok"] for x in r["rows"])
        print(f"{r['model']:<14}{r['acc']:>8.1%}{n_ok:>6}{len(r['rows']):>7}")


def main() -> None:
    problems = load_problems(DATA)
    print(f"problems: {len(problems)}\n")

    results = [evaluate(name, fn, problems) for name, fn in MODELS.items()]
    print_table(results)

    # 打印错了的题，方便做失败分析
    print("\nwrong answers:")
    for r in results:
        for x in r["rows"]:
            if not x["ok"]:
                print(f"  [{r['model']}] {x['id']}  pred={x['pred']!r}  gold={x['gold']!r}")

    out = ROOT / "results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
