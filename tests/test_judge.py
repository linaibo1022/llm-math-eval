"""judge.py 的单元测试。

覆盖三类行为：
1. extract_answer：从模型输出里抽出答案
2. normalize：规范化各种写法
3. is_correct：等价判断（分数、小数、多解、单位、表达式）

运行：
    python -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from judge import extract_answer, is_correct, normalize  # noqa: E402


class TestExtractAnswer(unittest.TestCase):
    def test_boxed_simple(self):
        self.assertEqual(extract_answer(r"\boxed{7}"), "7")

    def test_boxed_nested_frac(self):
        # 嵌套大括号，正则抓不住，必须配对括号
        self.assertEqual(extract_answer(r"\boxed{\frac{5}{6}}"), r"\frac{5}{6}")

    def test_boxed_with_prose(self):
        self.assertEqual(extract_answer(r"由通分得 \boxed{\frac{5}{6}}"), r"\frac{5}{6}")

    def test_answer_prefix(self):
        self.assertEqual(extract_answer("所以答案是 5"), "5")
        self.assertEqual(extract_answer("答案：5"), "5")

    def test_last_line_fallback(self):
        self.assertEqual(extract_answer("设 x=1\n代入得\n7"), "7")

    def test_empty(self):
        self.assertEqual(extract_answer(""), "")
        self.assertEqual(extract_answer("   \n  "), "")


class TestNormalize(unittest.TestCase):
    def test_unit_stripped(self):
        self.assertEqual(normalize("5 元"), "5")

    def test_multi_answer_separator(self):
        self.assertEqual(normalize("x=1 或 x=2"), "x=1,x=2")

    def test_fullwidth(self):
        self.assertEqual(normalize("＝5"), "=5")

    def test_dollar_stripped(self):
        self.assertEqual(normalize("$7$"), "7")


class TestIsCorrect(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(is_correct("5", "5"))

    def test_unit(self):
        self.assertTrue(is_correct("5 元", "5"))

    def test_frac_latex_equiv(self):
        self.assertTrue(is_correct(r"\frac{5}{6}", "5/6"))

    def test_decimal_fraction_equiv(self):
        self.assertTrue(is_correct("3/10", "0.3"))

    def test_decimal_not_exact(self):
        # 0.8333 是 5/6 的近似，不是精确值，不应判对
        self.assertFalse(is_correct("0.8333", "5/6"))

    def test_multi_answer_order_insensitive(self):
        self.assertTrue(is_correct("x=1 或 x=2", "x=2, x=1"))

    def test_expression_equiv(self):
        self.assertTrue(is_correct("1/2+1/3", "5/6"))
        self.assertTrue(is_correct("2^10", "1024"))

    def test_float_int(self):
        self.assertTrue(is_correct("7", "7.0"))

    def test_wrong(self):
        self.assertFalse(is_correct("4", "5"))
        self.assertFalse(is_correct("x=1", "x=2"))

    def test_empty_pred(self):
        self.assertFalse(is_correct("", "5"))


if __name__ == "__main__":
    unittest.main()
