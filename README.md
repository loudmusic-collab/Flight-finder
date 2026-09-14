# Cheapest Window Flight Finder

A free, personal-use tool that scans a route over the next ~9 months and
finds the cheapest N-day trip window, using Travelpayouts' cached price
calendar data.

## Setup

1. **Travelpayouts**
   - Sign up at https://www.travelpayouts.com as a partner.
   - Grab your API token from the dashboard.

2. **This repo**
   - Push this folder to a new GitHub repo.
   - In repo Settings → Secrets and variables → Actions, add a secret
     named `TRAVELPAYOUTS_TOKEN` with your token.
   - In repo Settings → Pages, set source to "Deploy from a branch",
     `main` branch, `/docs` folder. (Pages only supports `/` or `/docs`,
     not arbitrary folder names — that's why the site lives in `docs/`.)

3. **Edit your routes**
   - Open `scripts/search_flights.py` and edit the `ROUTES` list with the
     origin/destination/trip-length combos you actually want tracked.
     Each one becomes searchable on the site.

4. **Run it**
   - Locally: `export TRAVELPAYOUTS_TOKEN=your_token` then
     `python scripts/search_flights.py` to generate `docs/results.json`
     and sanity-check it before automating.
   - Automated: the GitHub Actions workflow
     (`.github/workflows/update-flights.yml`) runs daily and commits the
     refreshed `results.json` automatically. You can also trigger it
     manually from the repo's Actions tab.

5. **View it**
   - Once GitHub Pages is enabled, your site is live at
     `https://<your-username>.github.io/<repo-name>/`.
   - Type a city/airport in the From/To fields (autocompletes against
     `docs/airports.json`), pick a trip length that matches one of your
     configured routes, and hit search.

## Notes / next steps

- `docs/airports.json` currently has a starter list of ~45 major
  airports. Swap in the full open-source `airport-codes` dataset
  (trimmed to code/name/city/country) if you want broader autocomplete
  coverage.
- The Travelpayouts month-matrix endpoint returns *cached/aggregated*
  prices, not live bookable fares — great for "when's cheap," not for
  confirming an exact quote. Before booking, double-check the winning
  dates on the airline's site or an OTA.
