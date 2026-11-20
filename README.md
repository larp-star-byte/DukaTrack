# DukaTrack

AI demand-forecasting and stock-tracking web system for small Kenyan dukas (SSAD project, DBIT, Strathmore University).

## Run it
```
pip install -r Backend/requirements.txt
python Backend/seed.py        # creates the demo database with 120 days of sales
python Backend/app.py         # open http://localhost:5000
```
Logins: owner / Owner@123 (Shop Owner); amina / Attendant@123 and brian / Attendant@123 (Attendants).

Tests: `pytest -q Backend/tests` (18 tests). MySQL: set `DATABASE_URL=mysql+pymysql://user:pass@host/dukatrack` and run `Backend/schema.sql`.
Restore a backup: `python Backend/restore.py Backend/backups/<file>.json.gz`.

## Front end (class-style structure)
Pages are in `static/Frontend/`, including: `index.html` (login), `stock.html`, `forecast.html`, `sales.html`, `goods.html`, `products.html`, `reports.html`, `attendants.html`, `backup.html`.
Each page has header, nav, main, aside and footer, placed with CSS grid in `static/css/style.css`.
`static/js/main.js` holds the shared code (calling the server, who is logged in, messages). Each page has one small script of its own, for example `js/sales.js`.
Backend Python modules, tests, demo tools, schema, and requirements are grouped in `Backend/`. The server still checks the role on every request, so hiding links on the page is only for convenience.

## Demo order (about 5 minutes)
1. Wrong password, then the lockout message (FR01, NFR01).
2. Attendant: record a sale; try selling more than the stock (FR02, FR06).
3. Owner: Stock levels with low-stock flags; Enter goods; Products.
4. Forecast: 7 and 30 days, with "Short by N" against current stock (FR17 to FR19).
5. Sales: cancel a sale; Reports: day/week/month, CSV, accuracy table.
6. Attendants, then Backup.

## Forecasting
Holt-Winters (weekly seasonality) with 28 or more days of history, damped trend with 14 to 27 days, simple average with fewer. Accuracy is reported as MAE for finished forecast periods.

## Simplifications
SQLite by default; backups are gzip JSON files outside the web folder; no real mobile-money or SMS integration.
