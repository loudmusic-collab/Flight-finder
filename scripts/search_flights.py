"""
Cheapest-window flight finder — Travelpayouts edition.

Calls the Travelpayouts /v2/prices/month-matrix endpoint for each route/month
(once for the outbound direction, once for the return direction), then slides
a trip-length window across the results to find the cheapest depart/return
pair.

SETUP:
  1. Sign up at travelpayouts.com, grab your API token from the dashboard.
  2. Set it as an environment variable: export TRAVELPAYOUTS_TOKEN=your_token
  3. pip install requests
  4. Edit ROUTES below to match the trips you actually want tracked.
  5. Run: python search_flights.py
     -> writes docs/results.json
"""

import os
import json
import time
from datetime import date, timedelta
from pathlib import Path

import requests

# ---- Config ----
TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN")
CALENDAR_URL = "https://api.travelpayouts.com/v2/prices/month-matrix"
CURRENCY = "usd"
WINDOW_MONTHS = 9          # how far ahead to search
TOP_N = 10                 # how many cheapest windows to keep per route
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "results.json"

# Each entry: (origin, destination, trip_length_days)
ROUTES = [
    ("JFK", "CDG", 7),
    ("JFK", "LIS", 10),
    ("SFO", "NRT", 14),
]


def month_starts(n_months):
    """Yield the first-of-month date string for the next n_months, e.g. 2026-10."""
    today = date.today()
    y, m = today.year, today.month
    out = []
    for _ in range(n_months):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def fetch_month_prices(origin, destination, month_str):
    """Fetch cached one-way prices for one origin/destination/month.

    Returns {depart_date_str: cheapest_price}. The month-matrix endpoint
    returns a list of fare entries (one per day found, sometimes several
    per day for different routings) under "data", each with "depart_date"
    and "value" — not a dict keyed by date, and not "price".
    """
    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": month_str,
        "currency": CURRENCY,
        "show_to_affiliates": "false",
        "token": TOKEN,
    }
    resp = requests.get(CALENDAR_URL, params=params, timeout=20)
    resp.raise_for_status()
    entries = resp.json().get("data") or []

    lookup = {}
    for entry in entries:
        day = entry.get("depart_date")
        price = entry.get("value")
        if not day or not price:
            continue
        if day not in lookup or price < lookup[day]:
            lookup[day] = price
    return lookup


def build_price_lookup(origin, destination):
    """Returns {date_str: cheapest one-way price} across the full search window."""
    lookup = {}
    for month_str in month_starts(WINDOW_MONTHS):
        try:
            month_prices = fetch_month_prices(origin, destination, month_str)
        except requests.RequestException as e:
            print(f"  WARN: {origin}->{destination} {month_str} failed: {e}")
            continue
        lookup.update(month_prices)
        time.sleep(0.25)  # well within the 300/min limit, just being polite
    return lookup


def cheapest_windows(outbound_lookup, inbound_lookup, trip_length, top_n):
    """Slide a trip_length-day window across known depart dates.

    outbound_lookup holds origin->destination one-way prices by depart date;
    inbound_lookup holds destination->origin one-way prices by depart date
    (i.e. the return flight's own departure date). A window's total price is
    the outbound fare plus the matching inbound fare.
    """
    windows = []
    for depart_str, depart_price in outbound_lookup.items():
        return_date = date.fromisoformat(depart_str) + timedelta(days=trip_length)
        return_str = return_date.isoformat()
        return_price = inbound_lookup.get(return_str)
        if return_price is not None:
            windows.append({
                "depart": depart_str,
                "return": return_str,
                "price": round(depart_price + return_price, 2),
            })

    windows.sort(key=lambda w: w["price"])
    return windows[:top_n]


def main():
    if not TOKEN:
        raise SystemExit("Set TRAVELPAYOUTS_TOKEN before running this script.")

    route_results = []
    for origin, destination, trip_length in ROUTES:
        print(f"Fetching {origin} <-> {destination} ({trip_length} days)...")
        outbound = build_price_lookup(origin, destination)
        inbound = build_price_lookup(destination, origin)
        windows = cheapest_windows(outbound, inbound, trip_length, TOP_N)
        route_results.append({
            "origin": origin,
            "destination": destination,
            "trip_length": trip_length,
            "updated_at": date.today().isoformat(),
            "windows": windows,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump({"routes": route_results}, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
