#!/usr/bin/env python3
"""Convert the ReportHub "Windward Bin %" workbook into data.json for the scoreboard.

Usage: python3 scripts/build_data.py path/to/BinDroppedActual.xlsx [out=data.json]
"""
import json
import re
import sys
from datetime import datetime, timezone

import openpyxl


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(src, out="data.json"):
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

    data = {
        "days": days,
        "stores": stores,
        "system": system,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with open(out, "w") as f:
        json.dump(data, f, indent=1)
    print(f"Wrote {out}: {len(stores)} stores, latest day {days[-1]['date']} ({days[-1]['dow']})")


if __name__ == "__main__":
    main(*sys.argv[1:])
