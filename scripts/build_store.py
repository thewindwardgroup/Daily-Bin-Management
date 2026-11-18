#!/usr/bin/env python3
"""Refresh the store performance scoreboard (store/index.html) from PAR POS "Sales Summary.pdf" reports.

Each PAR POS store email carries a "Sales Summary.pdf". This script reads any number of them
(any stores, any business dates), stores net sales / order count / labor hours per store and day in
data/store-history.json, then writes the latest business date (with the day before it as the
comparison) into the <script id="sales-data"> block of store/index.html. The page itself is untouched.

Usage: python3 scripts/build_store.py "Sales Summary.pdf" [more PDFs ...]
       options: --history data/store-history.json  --page store/index.html  --goal 65
Needs `pdftotext` (poppler-utils).
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta

# Board order and display names (stores not listed are appended in id order).
STORES = [("74538", "West Point"), ("74394", "Philadelphia"), ("75041", "Tupelo"), ("74318", "Pontotoc")]


def money(s):
    return float(s.replace("$", "").replace(",", "").replace("(", "-").replace(")", ""))


def parse_pdf(path):
    txt = subprocess.run(["pdftotext", "-layout", "-l", "1", path, "-"],
                         capture_output=True, text=True, check=True).stdout
    head = txt.splitlines()[:3]
    if not head or "Sales Summary" not in head[0]:
        raise SystemExit(f"{path}: not a PAR Sales Summary report")
    loc = re.search(r"([A-Za-z]+)_(\d+)\s*$", head[0])
    day = re.search(r"[A-Za-z]+day, ([A-Za-z]+ \d{1,2}, \d{4})", "\n".join(head))
    if not loc or not day:
        raise SystemExit(f"{path}: couldn't read location / business date")

    def field(label):
        m = re.search(re.escape(label) + r":?\s+(\(?\$?[\d,]+\.?\d*\)?)", txt)
        if not m:
            raise SystemExit(f"{path}: '{label}' not found")
        return money(m.group(1))

    date = datetime.strptime(day.group(1), "%B %d, %Y").strftime("%m/%d/%Y")
    return {"id": loc.group(2), "loc": loc.group(1), "date": date,
            "sales": field("Net Sales"), "orders": int(field("Order Count")), "hours": field("Labor Hours")}


def name_for(sid, loc):
    for i, n in STORES:
        if i == sid:
            return n
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", loc)


def render(day, prev_day, hist, goal):
    order = [i for i, _ in STORES] + sorted(k for k in hist[day] if k not in dict(STORES))
    lines = []
    for sid in order:
        r = hist[day].get(sid)
        if not r:
            continue
        s = ('{"name":%s,"id":%s,"sales":%.2f,"orders":%d,"hours":%.2f'
             % (json.dumps(r["name"]), json.dumps(sid), r["sales"], r["orders"], r["hours"]))
        p = hist.get(prev_day, {}).get(sid) if prev_day else None
        if p:
            s += ',"prev":{"sales":%.2f,"orders":%d,"hours":%.2f}' % (p["sales"], p["orders"], p["hours"])
        lines.append(" " + s + "}")
    prev_dow = datetime.strptime(prev_day, "%m/%d/%Y").strftime("%a") if prev_day else ""
    g = int(goal) if float(goal).is_integer() else goal
    return ('{"date":%s,"prevDow":%s,"splhGoal":%s,\n"stores":[\n%s\n]}\n'
            % (json.dumps(day), json.dumps(prev_dow), g, ",\n".join(lines)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="*")
    ap.add_argument("--history", default="data/store-history.json")
    ap.add_argument("--page", default="store/index.html")
    ap.add_argument("--goal", type=float, default=65)
    a = ap.parse_args()

    hist = json.load(open(a.history)) if os.path.exists(a.history) else {}
    for p in a.pdfs:
        r = parse_pdf(p)
        hist.setdefault(r["date"], {})[r["id"]] = {
            "name": name_for(r["id"], r["loc"]), "sales": r["sales"], "orders": r["orders"], "hours": r["hours"]}
        print(f"  {r['date']} {r['loc']}_{r['id']}: ${r['sales']:,.2f}, {r['orders']} orders, {r['hours']} hrs")
    if not hist:
        raise SystemExit("No data")

    key = lambda d: datetime.strptime(d, "%m/%d/%Y")
    dates = sorted(hist, key=key)
    day = dates[-1]
    want_prev = (key(day) - timedelta(days=1)).strftime("%m/%d/%Y")
    prev_day = want_prev if want_prev in hist else None

    # keep ~60 days of history
    for d in dates[:-60]:
        del hist[d]
    os.makedirs(os.path.dirname(a.history) or ".", exist_ok=True)
    with open(a.history, "w") as f:
        json.dump({d: hist[d] for d in sorted(hist, key=key)}, f, indent=1, sort_keys=False)
        f.write("\n")

    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_data import embed
    embed(a.page, "sales-data", render(day, prev_day, hist, a.goal))
    print(f"Updated {a.page}: {len(hist[day])} stores for {day}"
          + (f" vs {prev_day}" if prev_day else " (no prior-day data)"))


if __name__ == "__main__":
    main()
