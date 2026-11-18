# Windward Scoreboards

Two 1920×1080 TV scoreboards (scale to any screen, reload every 30 min), served by GitHub Pages:

- **Bin Management** — https://thewindwardgroup.github.io/Daily-Bin-Management/ (`index.html`)
- **Store Performance** — https://thewindwardgroup.github.io/Daily-Bin-Management/store/ (`store/index.html`)

Each page carries its data in an embedded `<script type="application/json">` block. The scripts below
replace only that block, so the pages themselves never change.

| Script | Source | Updates |
|---|---|---|
| `scripts/build_data.py BinDroppedActual.xlsx` | ReportHub "Windward Bin %" email (.xlsx) | `index.html` |
| `scripts/build_store.py "Sales Summary.pdf" ...` | PAR POS store emails (`Sales Summary.pdf`, one per store) | `store/index.html` + `data/store-history.json` |

`build_store.py` keeps net sales / orders / labor hours per store per day in `data/store-history.json`,
so the day-over-day comparison only needs that day's four PDFs. It needs `pdftotext` (poppler-utils);
`build_data.py` needs `openpyxl`.

A scheduled task runs both every morning around 10:30 AM Eastern and pushes the result.
