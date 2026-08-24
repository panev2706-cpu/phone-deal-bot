"""Fixture-based tests for marketplace HTML parsers.

These tests never make a network request.  The snapshots intentionally contain
duplicate and incomplete cards because both are common in marketplace pages.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import unittest

from scrapers.bazar import BazarScraper
from scrapers.olx import OlxScraper


FIXTURES = Path(__file__).with_name("fixtures")


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class BazarParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.results = BazarScraper().parse_search_results(
            fixture("bazar_search.html"),
            source_url="https://bazar.bg/obiavi?q=iphone",
        )

    def test_extracts_priced_cards_and_stable_ids(self) -> None:
        priced = {item.listing_id: item for item in self.results if item.price_amount is not None}
        self.assertEqual({"12345", "67890"}, set(priced))

        iphone = priced["12345"]
        self.assertEqual("bazar", iphone.marketplace.lower())
        self.assertEqual("iPhone 14 Pro Max 256GB", iphone.title)
        self.assertEqual(Decimal("780"), iphone.price_amount)
        self.assertEqual("BGN", iphone.currency)

        samsung = priced["67890"]
        self.assertEqual(Decimal("499.99"), samsung.price_amount)
        self.assertEqual("EUR", samsung.currency)

    def test_normalizes_urls_images_and_locations(self) -> None:
        items = {item.listing_id: item for item in self.results if item.price_amount is not None}
        self.assertEqual(
            "https://bazar.bg/obiava-12345/iphone-14-pro-max-256gb",
            items["12345"].url,
        )
        self.assertEqual("https://img.bazar.bg/iphone-14.jpg", items["12345"].image_url)
        self.assertIn("София", items["12345"].location or "")
        self.assertEqual("https://img.bazar.bg/s24-ultra.jpg", items["67890"].image_url)
        self.assertIn("Пловдив", items["67890"].location or "")

    def test_duplicate_card_does_not_duplicate_listing(self) -> None:
        ids = [item.listing_id for item in self.results if item.price_amount is not None]
        self.assertEqual(len(ids), len(set(ids)))

    def test_empty_page_is_valid(self) -> None:
        self.assertEqual([], BazarScraper().parse_search_results("<html></html>"))

    def test_json_ld_is_a_fallback_when_card_markup_changes(self) -> None:
        results = BazarScraper().parse_search_results(fixture("bazar_jsonld.html"))
        self.assertEqual(1, len(results))
        item = results[0]
        self.assertEqual("24680", item.listing_id)
        self.assertEqual(Decimal("450.25"), item.price_amount)
        self.assertEqual("EUR", item.currency)
        self.assertEqual("https://img.bazar.bg/json-iphone.jpg", item.image_url)
        self.assertIn("отлично", item.description or "")


class OlxParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.results = OlxScraper().parse_search_results(
            fixture("olx_search.html"),
            source_url="https://www.olx.bg/elektronika/telefoni/?q=iphone",
        )

    def test_extracts_priced_cards_and_ids(self) -> None:
        priced = {item.listing_id: item for item in self.results if item.price_amount is not None}
        self.assertEqual({"abc123", "xyz789"}, set(priced))

        iphone = priced["abc123"]
        self.assertEqual("olx", iphone.marketplace.lower())
        self.assertEqual("iPhone 15 Pro 256GB", iphone.title)
        self.assertEqual(Decimal("1050"), iphone.price_amount)
        self.assertEqual("BGN", iphone.currency)

        samsung = priced["xyz789"]
        self.assertEqual(Decimal("525.50"), samsung.price_amount)
        self.assertEqual("EUR", samsung.currency)

    def test_normalizes_urls_images_and_locations(self) -> None:
        items = {item.listing_id: item for item in self.results if item.price_amount is not None}
        self.assertEqual(
            "https://www.olx.bg/d/obyava/iphone-15-pro-256gb-IDabc123.html",
            items["abc123"].url,
        )
        self.assertEqual("https://apollo.olxcdn.com/iphone-15.jpg", items["abc123"].image_url)
        self.assertIn("Варна", items["abc123"].location or "")
        self.assertEqual("https://apollo.olxcdn.com/s24.jpg", items["xyz789"].image_url)
        self.assertIn("София", items["xyz789"].location or "")

    def test_duplicate_card_does_not_duplicate_listing(self) -> None:
        ids = [item.listing_id for item in self.results if item.price_amount is not None]
        self.assertEqual(len(ids), len(set(ids)))

    def test_empty_page_is_valid(self) -> None:
        self.assertEqual([], OlxScraper().parse_search_results("<html></html>"))

    def test_json_ld_is_a_fallback_when_card_markup_changes(self) -> None:
        results = OlxScraper().parse_search_results(fixture("olx_jsonld.html"))
        self.assertEqual(1, len(results))
        item = results[0]
        self.assertEqual("json321", item.listing_id)
        self.assertEqual(Decimal("999"), item.price_amount)
        self.assertEqual("BGN", item.currency)
        self.assertEqual("https://apollo.olxcdn.com/json-s24.jpg", item.image_url)
        self.assertIn("Русе", item.location or "")
        self.assertIn("Пълен", item.description or "")

    def test_accepts_current_d_ad_listing_url_variant(self) -> None:
        results = OlxScraper().parse_search_results(
            fixture("olx_ad_link.html"), source_url="https://www.olx.bg/ads/q-iphone/"
        )
        self.assertEqual(1, len(results))
        item = results[0]
        self.assertEqual("newAd77", item.listing_id)
        self.assertEqual(
            "https://www.olx.bg/d/ad/iphone-14-pro-max-IDnewAd77.html", item.url
        )
        self.assertEqual(Decimal("980"), item.price_amount)
        self.assertEqual("BGN", item.currency)
        self.assertIn("Благоевград", item.location or "")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
