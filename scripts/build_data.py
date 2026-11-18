#!/usr/bin/env python3
"""Refresh the bin scoreboard (index.html) from the ReportHub "Windward Bin %" workbook.

Only the <script id="bin-data"> JSON block in index.html is replaced; the page itself is untouched.

Usage: python3 scripts/build_data.py path/to/BinDroppedActual.xlsx [page=index.html]
"""
import json
import re
import sys

import openpyxl


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse(src):
    ws = openpyxl.load_workbook(src, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]

    # Day columns are the headers that contain a date, e.g. "Actual Dropped % \n11/17/2026\nTuesday"
    day_cols, days = [], []
    for i, h in enumerate(header):
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*\n?\s*([A-Za-z]+)?", str(h or ""))
        if m:
            day_cols.append(i)
            days.append({"date": m.group(1), "dow": (m.group(2) or "").strip()})
    if not days:
        raise SystemExit("No date columns found in the report header")

    def vals(r):
        return [num(r[i]) for i in day_cols]

    stores, system, cur = [], None, None
    for r in rows[1:]:
        a = (r[0] or "").strip() if isinstance(r[0], str) else r[0]
        b = (r[1] or "").strip() if isinstance(r[1], str) else r[1]
        if a:
            if str(a).lower().startswith("system average"):
                system = vals(r)
                cur = None
                continue
            m = re.match(r"(.+?)_(\d+)$", str(a))
            name, sid = (m.group(1), m.group(2)) if m else (str(a), "")
            cur = {"id": sid, "name": name.replace("_", " ").title(), "overall": vals(r), "dayparts": []}
            stores.append(cur)
        elif b and cur is not None:
            cur["dayparts"].append({"name": str(b), "vals": vals(r)})

    if not stores:
        raise SystemExit("No stores found in the report")
    return {"days": days, "stores": stores, "system": system}


def embed(page, block_id, text):
    html = open(page, encoding="utf-8").read()
    pat = re.compile(r'(<script id="' + block_id + r'" type="application/json">)(.*?)(</script>)', re.S)
    if not pat.search(html):
        raise SystemExit(f'No <script id="{block_id}"> block in {page}')
    if "</" in text:
        raise SystemExit("Data contains '</' and can't be embedded safely")
    html = pat.sub(lambda m: m.group(1) + text + m.group(3), html, count=1)
    with open(page, "w", encoding="utf-8") as f:
        f.write(html)


def main(src, page="index.html"):
    data = parse(src)
    embed(page, "bin-data", json.dumps(data))
    d = data["days"][-1]
    print(f"Updated {page}: {len(data['stores'])} stores, latest day {d['date']} ({d['dow']})")


if __name__ == "__main__":
    main(*sys.argv[1:])
