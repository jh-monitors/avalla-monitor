#!/usr/bin/env python3
"""
Avalla refurbished air-conditioner monitor.

Designed for GitHub Actions. It checks Avalla's Shopify collection JSON,
filters out accessories, compares the result with state.json, and sends a
Discord alert for:
  - a newly listed genuine air conditioner that is in stock
  - an existing genuine air conditioner that changes from sold out to in stock

No third-party Python packages are required.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read {path.name}: {exc}", file=sys.stderr)
        return default


def save_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def fetch_json(url: str, retries: int = 3) -> dict[str, Any]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/149 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"Unexpected HTTP status {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError, RuntimeError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Unable to read Avalla after {retries} attempts: {exc}") from exc
            wait_seconds = attempt * 5
            print(f"Fetch attempt {attempt} failed; retrying in {wait_seconds}s: {exc}")
            time.sleep(wait_seconds)

    raise RuntimeError("Fetch failed unexpectedly")


def normalise(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").split())


def is_genuine_air_conditioner(product: dict[str, Any], config: dict[str, Any]) -> bool:
    title = normalise(str(product.get("title", "")))
    handle = normalise(str(product.get("handle", "")))
    combined = f"{title} {handle}"

    excluded = [normalise(word) for word in config.get("excludeKeywords", [])]
    if any(word and word in combined for word in excluded):
        return False

    included = [normalise(word) for word in config.get("includeKeywords", [])]
    return any(word and word in combined for word in included)


def product_available(product: dict[str, Any]) -> bool:
    variants = product.get("variants") or []
    return any(bool(variant.get("available")) for variant in variants)


def format_price(product: dict[str, Any]) -> str:
    prices: list[float] = []
    for variant in product.get("variants") or []:
        raw = variant.get("price")
        try:
            prices.append(float(raw))
        except (TypeError, ValueError):
            continue

    if not prices:
        return "Price unavailable"

    low, high = min(prices), max(prices)
    if low == high:
        return f"£{low:,.2f}"
    return f"£{low:,.2f}–£{high:,.2f}"


def compact_product(product: dict[str, Any], store_url: str) -> dict[str, Any]:
    handle = str(product.get("handle", "")).strip()
    return {
        "id": str(product.get("id", handle)),
        "title": str(product.get("title", "Untitled product")).strip(),
        "handle": handle,
        "url": f"{store_url.rstrip('/')}/products/{handle}",
        "available": product_available(product),
        "price": format_price(product),
    }


def discord_post(webhook_url: str, payload: dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Avalla-Cloud-Monitor/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status not in (200, 204):
                raise RuntimeError(f"Discord returned HTTP {response.status}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"Unable to send Discord alert: {exc}") from exc


def send_stock_alert(webhook_url: str, product: dict[str, Any], event: str) -> None:
    heading = (
        "🚨 New Avalla air conditioner in stock"
        if event == "new"
        else "🚨 Avalla air conditioner restocked"
    )
    payload = {
        "username": "Avalla AC Monitor",
        "content": heading,
        "embeds": [
            {
                "title": product["title"],
                "url": product["url"],
                "description": "**Status:** IN STOCK",
                "fields": [
                    {"name": "Price", "value": product["price"], "inline": True},
                    {"name": "Event", "value": "New listing" if event == "new" else "Restock", "inline": True},
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "allowed_mentions": {"parse": []},
    }
    discord_post(webhook_url, payload)


def send_test_alert(webhook_url: str) -> None:
    discord_post(
        webhook_url,
        {
            "username": "Avalla AC Monitor",
            "content": "✅ Test successful — your cloud Avalla monitor can send Discord alerts.",
            "allowed_mentions": {"parse": []},
        },
    )


def main() -> int:
    config = load_json(CONFIG_PATH, {})
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        print(
            "DISCORD_WEBHOOK_URL is missing. Add it as a GitHub Actions repository secret.",
            file=sys.stderr,
        )
        return 2

    if os.environ.get("TEST_NOTIFICATION", "").lower() == "true":
        send_test_alert(webhook_url)
        print("Discord test notification sent.")
        return 0

    collection_url = str(config.get("collectionJsonUrl", "")).strip()
    store_url = str(config.get("storeUrl", "https://www.avalla.com")).strip()
    if not collection_url:
        print("collectionJsonUrl is missing from config.json.", file=sys.stderr)
        return 2

    response = fetch_json(collection_url)
    raw_products = response.get("products")
    if not isinstance(raw_products, list):
        raise RuntimeError("Avalla response did not contain a products list")

    products = [
        compact_product(product, store_url)
        for product in raw_products
        if isinstance(product, dict) and is_genuine_air_conditioner(product, config)
    ]

    previous_state = load_json(STATE_PATH, {})
    previous_products = previous_state.get("products", {}) if isinstance(previous_state, dict) else {}
    first_run = not bool(previous_state.get("initialised")) if isinstance(previous_state, dict) else True

    current_by_id = {product["id"]: product for product in products}
    alerts: list[tuple[dict[str, Any], str]] = []

    if not first_run:
        for product_id, product in current_by_id.items():
            previous = previous_products.get(product_id)
            if previous is None and product["available"]:
                alerts.append((product, "new"))
            elif previous is not None and not previous.get("available", False) and product["available"]:
                alerts.append((product, "restock"))

    for product, event in alerts:
        send_stock_alert(webhook_url, product, event)
        print(f"Sent {event} alert: {product['title']}")

    new_state = {
        "initialised": True,
        "lastCheckedUtc": datetime.now(timezone.utc).isoformat(),
        "products": current_by_id,
    }
    save_json(STATE_PATH, new_state)

    in_stock = sum(1 for product in products if product["available"])
    print(
        f"Check complete: {len(products)} genuine AC listing(s), "
        f"{in_stock} in stock, {len(alerts)} alert(s)."
    )
    if first_run:
        print("Initial baseline saved. Existing products were not alerted.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Monitor failed: {exc}", file=sys.stderr)
        raise
