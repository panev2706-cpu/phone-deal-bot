"""Strict, beginner-friendly JSON configuration loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class SearchConfig:
    name: str
    keywords: tuple[str, ...]
    max_price_eur: Decimal


@dataclass(frozen=True)
class AppConfig:
    enabled_marketplaces: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    searches: tuple[SearchConfig, ...]
    good_deal_percent: Decimal = Decimal("10")
    great_deal_percent: Decimal = Decimal("20")
    request_timeout_seconds: int = 20
    request_retries: int = 2
    request_delay_seconds: float = 1.0
    pages_per_search: int = 1
    health_alert_after_failures: int = 3


def _nonempty_strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f'"{field}" must be a non-empty JSON list of text values.')
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f'"{field}[{index}]" must be non-empty text.')
        result.append(item.strip())
    return tuple(result)


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ConfigError(f'"{field}" must be a number.')
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ConfigError(f'"{field}" must be a number.') from None
    if not number.is_finite():
        raise ConfigError(f'"{field}" must be a finite number.')
    return number


def _bounded_int(data: dict[str, Any], field: str, default: int, low: int, high: int) -> int:
    value = data.get(field, default)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ConfigError(f'"{field}" must be a whole number from {low} to {high}.')
    return value


def load_config(path: str | Path = "config.json") -> AppConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}.") from None
    if not isinstance(raw, dict):
        raise ConfigError("The top level of config.json must be a JSON object.")

    allowed_marketplaces = {"olx", "bazar", "alo"}
    marketplaces = _nonempty_strings(
        raw.get("enabled_marketplaces", ["bazar", "alo"]), "enabled_marketplaces"
    )
    unknown = sorted(set(marketplaces) - allowed_marketplaces)
    if unknown:
        raise ConfigError(f"Unknown marketplace(s): {', '.join(unknown)}.")
    if len(set(marketplaces)) != len(marketplaces):
        raise ConfigError('"enabled_marketplaces" contains duplicates.')

    excludes_raw = raw.get("exclude_keywords", [])
    if not isinstance(excludes_raw, list) or any(
        not isinstance(item, str) or not item.strip() for item in excludes_raw
    ):
        raise ConfigError('"exclude_keywords" must be a JSON list of non-empty text values.')
    excludes = tuple(item.strip() for item in excludes_raw)

    searches_raw = raw.get("searches")
    if not isinstance(searches_raw, list) or not searches_raw:
        raise ConfigError('"searches" must contain at least one phone search.')
    searches: list[SearchConfig] = []
    for index, item in enumerate(searches_raw):
        prefix = f"searches[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f'"{prefix}" must be a JSON object.')
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f'"{prefix}.name" must be non-empty text.')
        keywords = _nonempty_strings(item.get("keywords"), f"{prefix}.keywords")
        maximum = _decimal(item.get("max_price_eur"), f"{prefix}.max_price_eur")
        if maximum <= 0:
            raise ConfigError(f'"{prefix}.max_price_eur" must be greater than zero.')
        searches.append(SearchConfig(name.strip(), keywords, maximum))

    good = _decimal(raw.get("good_deal_percent", 10), "good_deal_percent")
    great = _decimal(raw.get("great_deal_percent", 20), "great_deal_percent")
    if good < 0 or great <= good or great > 100:
        raise ConfigError(
            'Deal percentages must satisfy 0 <= "good_deal_percent" '
            '< "great_deal_percent" <= 100.'
        )

    timeout = _bounded_int(raw, "request_timeout_seconds", 20, 5, 120)
    retries = _bounded_int(raw, "request_retries", 2, 0, 5)
    pages = _bounded_int(raw, "pages_per_search", 1, 1, 5)
    health_after = _bounded_int(raw, "health_alert_after_failures", 3, 1, 20)
    delay_value = raw.get("request_delay_seconds", 1.0)
    if isinstance(delay_value, bool) or not isinstance(delay_value, (int, float)) or not 0 <= delay_value <= 30:
        raise ConfigError('"request_delay_seconds" must be a number from 0 to 30.')

    return AppConfig(
        enabled_marketplaces=marketplaces,
        exclude_keywords=excludes,
        searches=tuple(searches),
        good_deal_percent=good,
        great_deal_percent=great,
        request_timeout_seconds=timeout,
        request_retries=retries,
        request_delay_seconds=float(delay_value),
        pages_per_search=pages,
        health_alert_after_failures=health_after,
    )
