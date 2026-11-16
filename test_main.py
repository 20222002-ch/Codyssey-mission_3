"""기본 계산과 보너스 기능 검증. 실행: py -m unittest -v"""
import contextlib
import copy
import io
import random
import unittest
from unittest.mock import patch

import main


class BonusTests(unittest.TestCase):
    def test_generated_three_by_three(self):
        self.assertEqual(main.make_cross(3), [[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        self.assertEqual(main.make_x(3), [[1, 0, 1], [0, 1, 0], [1, 0, 1]])

    def test_generated_sizes_and_even_center(self):
        self.assertEqual(main.make_cross(4), [
            [0, 0, 1, 0], [0, 0, 1, 0], [1, 1, 1, 1], [0, 0, 1, 0],
        ])
        self.assertEqual(main.make_x(4), [
            [1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1],
        ])
        for size in (1, 3, 5, 13, 25):
            self.assertEqual(sum(map(sum, main.make_cross(size))), 2 * size - 1)
            self.assertEqual(sum(map(sum, main.make_x(size))), 2 * size - 1)

    def test_invalid_sizes(self):
        for size in (0, -1, 2.5, True, "3"):
            for generate in (main.make_cross, main.make_x):
                with self.subTest(size=size, function=generate.__name__):
                    with self.assertRaises(ValueError):
                        generate(size)

    def test_flatten_row_order(self):
        self.assertEqual(main.flatten_matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), list(range(1, 10)))

    def test_known_mac_and_length_error(self):
        self.assertEqual(main.mac_flat(list(range(1, 10)), list(range(1, 10))), 285)
        self.assertEqual(main.mac_flat([1.5, -2, 0.25], [2, 3, -4]), -4)
        with self.assertRaises(ValueError):
            main.mac_flat([1, 2], [1])

    def test_flat_mac_matches_real_patterns_and_decimal_data(self):
        rng = random.Random(3)
        for size in (1, 3, 5, 13, 25):
            values = [[rng.uniform(-3, 3) for _ in range(size)] for _ in range(size)]
            weights = [[rng.uniform(-2, 2) for _ in range(size)] for _ in range(size)]
            self.assertEqual(main.mac(values, weights), main.mac_flat(
                main.flatten_matrix(values), main.flatten_matrix(weights),
            ))
        cross, x = main.make_cross(3), main.make_x(3)
        self.assertEqual(main.mac_flat(main.flatten_matrix(cross), main.flatten_matrix(x)), 1)

    def test_benchmark_input_repeat_and_score(self):
        values, weights = main.make_cross(5), main.make_cross(5)
        original = copy.deepcopy((values, weights))
        with patch.object(main, "mac", wraps=main.mac) as two_d:
            with patch.object(main, "mac_flat", wraps=main.mac_flat) as one_d:
                result = main.compare_mac(values, weights, repeat=10)
        # 정확성 확인 1회 + 측정 10회씩 동일하게 호출되어야 한다.
        self.assertEqual(two_d.call_count, 11)
        self.assertEqual(one_d.call_count, 11)
        self.assertEqual((values, weights), original)
        self.assertEqual(result["repeat"], 10)
        self.assertEqual(result["score_2d"], 9)
        self.assertEqual(result["score_1d"], 9)
        for key in ("time_2d_ms", "time_1d_ms", "conversion_ms"):
            self.assertGreaterEqual(result[key], 0)
        for repeat in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                main.compare_mac(values, weights, repeat)

    def test_manual_can_reuse_generated_filters_and_pattern(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["cross", "x", "x"]):
            with contextlib.redirect_stdout(output):
                main.run_manual()
        self.assertIn("A 점수: 1.0", output.getvalue())
        self.assertIn("B 점수: 5.0", output.getvalue())
        self.assertIn("판정: B", output.getvalue())

    def test_generator_retries_and_classifies(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["abc", "0", "1001", "5"]):
            with contextlib.redirect_stdout(output):
                main.run_generator()
        text = output.getvalue()
        self.assertEqual(text.count("사이의 정수를 입력하세요."), 3)
        self.assertIn("Cross 입력: Cross=9, X=1, 판정=Cross", text)
        self.assertIn("X 입력: Cross=1, X=9, 판정=X", text)
        self.assertIn("100회 평균", text)

    def test_one_cell_tie_and_large_preview(self):
        output = io.StringIO()
        with patch("builtins.input", return_value="1"):
            with contextlib.redirect_stdout(output):
                main.run_generator()
        self.assertEqual(output.getvalue().count("판정=UNDECIDED"), 2)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main.print_matrix(main.make_x(26))
        self.assertIn("26×26 배열 생성 완료", output.getvalue())


if __name__ == "__main__":
    unittest.main()
