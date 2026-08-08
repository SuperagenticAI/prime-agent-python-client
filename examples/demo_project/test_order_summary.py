from __future__ import annotations

import unittest

from order_summary import summarize_orders


class OrderSummaryTests(unittest.TestCase):
    def test_summarizes_orders(self) -> None:
        self.assertEqual(
            summarize_orders([10.0, 20.555, 4.445]),
            {"count": 3, "total": 35.0, "average": 11.67},
        )

    def test_empty_orders(self) -> None:
        self.assertEqual(
            summarize_orders([]),
            {"count": 0, "total": 0.0, "average": 0.0},
        )


if __name__ == "__main__":
    unittest.main()
