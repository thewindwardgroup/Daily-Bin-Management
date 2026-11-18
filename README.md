# Daily Bin Management

Windward Group bin-drop scoreboard, served by GitHub Pages:
https://thewindwardgroup.github.io/Daily-Bin-Management/

- `index.html` — the scoreboard (1920×1080, scales to any screen, reloads every 30 min)
- `data.json` — the latest data, regenerated each morning from the ReportHub "Windward Bin %" email
- `scripts/build_data.py` — converts the ReportHub .xlsx into `data.json`

Manual update: `python3 scripts/build_data.py BinDroppedActual.xlsx data.json`, then commit and push.
