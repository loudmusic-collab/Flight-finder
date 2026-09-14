# Flight Finder — Handoff Brief for Claude Code

## What this is
A personal, free-tier flight price tool for Jared and his partner. Given
an origin, destination, and trip length, it scans ~9 months of cached
price data and surfaces the cheapest depart/return date pairs. Static
site + scheduled script, no paid services.

## Repo
`github.com/loudmusic-collab/Flight-finder`

## Current file structure
```
Flight-finder/
├── README.md
├── docs/
│   ├── index.html      # form + autocomplete UI
│   ├── app.js           # autocomplete + results rendering
│   └── airports.json    # ~45 starter airports for autocomplete
├── scripts/
│   └── search_flights.py   # calls Travelpayouts month-matrix API, writes docs/results.json
└── .github/
    └── workflows/
        └── update-flights.yml   # daily cron + manual trigger, runs the script and commits results.json
```

## Fixed in this pass
- **Pages folder issue**: renamed `site/` → `docs/` throughout (script
  output path, workflow's `git add`, README), so GitHub Pages can serve
  it from `main` / `/docs`.
- **Wrong API endpoint/response shape**: the script was calling
  `v1/prices/calendar` and assuming `data` was a dict keyed by date with
  a `"price"` field. The actual endpoint for this use case is
  `v2/prices/month-matrix`, which returns `data` as a **list** of
  entries shaped like `{"depart_date": "...", "value": ...}`. Updated
  `fetch_month_prices` to match, keeping the cheapest fare when a date
  has multiple entries.
- **Cross-direction pricing bug**: the original `cheapest_windows` added
  two origin→destination one-way prices together (once for the "depart"
  date, once for the "return" date) — the return leg was never priced in
  the destination→origin direction. Now `search_flights.py` fetches both
  directions separately (`build_price_lookup(origin, destination)` and
  `build_price_lookup(destination, origin)`) and combines an outbound
  fare with a same-window inbound fare.
- Verified the new parsing/window logic offline against mocked API
  responses (duplicate-date de-dup, correct depart/return pairing).

## API / secrets status — still needs you
- Travelpayouts API token has already been obtained (via their
  Data API request flow, not fully self-serve — access was granted).
- **The token was pasted in plaintext in a prior chat conversation and
  should be treated as compromised.** Before going further:
  1. Rotate/regenerate the token in the Travelpayouts dashboard.
  2. Add the NEW token as a GitHub repo secret named
     `TRAVELPAYOUTS_TOKEN` (Settings → Secrets and variables → Actions).
  3. Never commit the token to any file in the repo.

## Remaining tasks (manual, need repo/dashboard access this session doesn't have)
1. Rotate the Travelpayouts token and add it as the `TRAVELPAYOUTS_TOKEN`
   GitHub secret (see above).
2. Enable GitHub Pages: Settings → Pages → source `main` branch, `/docs`
   folder.
3. Edit the `ROUTES` list in `scripts/search_flights.py` to the actual
   routes Jared wants tracked (currently placeholder routes:
   JFK→CDG, JFK→LIS, SFO→NRT).
4. Run the script once locally (`export TRAVELPAYOUTS_TOKEN=...` then
   `python scripts/search_flights.py`) or trigger the GitHub Action
   manually to confirm `docs/results.json` generates correctly with a
   real token — this pass only verified the logic against mocked
   responses, not the live API.
5. Confirm the live Pages URL works end-to-end: autocomplete → search →
   results display.

## Design decisions already made (don't relitigate unless asked)
- Data source: Travelpayouts Data API (free), not Amadeus (shut down
  for new devs) or Duffel (kept as a possible future live-price
  confirmation step, not needed for MVP).
- Airport autocomplete: static bundled JSON, not a live autocomplete
  API call (simpler, no network dependency while typing).
- Search strategy: script scans the full window directly (daily
  granularity) rather than a two-pass weekly-then-daily approach,
  since Travelpayouts' rate limit (300 req/min) comfortably covers a
  9-month single-pass scan per direction.
- Hosting: GitHub Pages + GitHub Actions cron, entirely free, no
  separate hosting account needed.
