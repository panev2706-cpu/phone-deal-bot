"""Configuration tests focused on errors a beginner can correct."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.config import ConfigError, load_config


def valid_config() -> dict:
    return {
        "enabled_marketplaces": ["olx", "bazar"],
        "exclude_keywords": ["case", "калъф"],
        "searches": [
            {
                "name": "iPhone 15 Pro",
                "keywords": ["iphone 15 pro"],
                "max_price_eur": 550,
            }
        ],
    }


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.json"

    def write(self, value: object) -> None:
        self.path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_loads_searches_as_typed_values_and_defaults(self) -> None:
        self.write(valid_config())
        config = load_config(self.path)
        self.assertEqual(("olx", "bazar"), config.enabled_marketplaces)
        self.assertEqual(("case", "калъф"), config.exclude_keywords)
        self.assertEqual("iPhone 15 Pro", config.searches[0].name)
        self.assertEqual(("iphone 15 pro",), config.searches[0].keywords)
        self.assertEqual(Decimal("550"), config.searches[0].max_price_eur)
        self.assertEqual(Decimal("10"), config.good_deal_percent)
        self.assertEqual(Decimal("20"), config.great_deal_percent)

    def test_shipped_config_is_valid(self) -> None:
        repository_config = Path(__file__).parents[1] / "config.json"
        self.assertTrue(load_config(repository_config).searches)

    def test_invalid_json_reports_line_and_column(self) -> None:
        self.path.write_text('{"searches": [}', encoding="utf-8")
        with self.assertRaisesRegex(ConfigError, r"line \d+, column \d+"):
            load_config(self.path)

    def test_missing_file_is_explained(self) -> None:
        with self.assertRaisesRegex(ConfigError, "Configuration file not found"):
            load_config(self.path)

    def test_rejects_unknown_or_duplicate_marketplaces(self) -> None:
        data = valid_config()
        data["enabled_marketplaces"] = ["olx", "example"]
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "Unknown marketplace"):
            load_config(self.path)

        data["enabled_marketplaces"] = ["olx", "olx"]
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "duplicates"):
            load_config(self.path)

    def test_rejects_missing_searches_and_invalid_search_fields(self) -> None:
        data = valid_config()
        data["searches"] = []
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "at least one phone search"):
            load_config(self.path)

        data["searches"] = [{"name": "Phone", "keywords": [], "max_price_eur": 500}]
        self.write(data)
        with self.assertRaisesRegex(ConfigError, r"searches\[0\]\.keywords"):
            load_config(self.path)

        data["searches"] = [{"name": "Phone", "keywords": ["phone"], "max_price_eur": 0}]
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "greater than zero"):
            load_config(self.path)

    def test_rejects_invalid_deal_threshold_order(self) -> None:
        data = valid_config()
        data.update({"good_deal_percent": 20, "great_deal_percent": 10})
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "percentages"):
            load_config(self.path)

    def test_rejects_out_of_range_request_settings(self) -> None:
        data = valid_config()
        data["request_retries"] = 99
        self.write(data)
        with self.assertRaisesRegex(ConfigError, "request_retries"):
            load_config(self.path)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
