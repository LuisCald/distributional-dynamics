"""Rebuild the Data Explorer's embedded data (const DATA in index.html; data/bivar.json)
from the published data products, so the charts match the downloads.

    python3 tools/build_explorer_data.py            # reads data/dd_series.csv, data/dd_master.csv

DATA        univariate, PSID view, decile groups D1..D10: share of total, group total (trillions of
            2019Q4 USD) and mean per household (2019Q4 USD; the `quantile_*` columns), 1962-Q3 onward.
BIVAR_DATA  bivariate: 10x10 population shares of decile cells (C x I, C x W, I x W), obtained by
            summing the synthetic-microdata copula grid (dd_master.csv, cop_share) over the third
            variable; quarters where the full C x I x W grid exists (PSID consumption, 1999-Q2 on).
"""
import json, os, re
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
series = pd.read_csv(os.path.join(ROOT, "data", "dd_series.csv"))
master = pd.read_csv(os.path.join(ROOT, "data", "dd_master.csv"))

def clean(a, nd):
    return [None if not np.isfinite(x) else round(float(x), nd) for x in a]

V = ["consum", "income", "wealth"]
P = [f"0.{k}" for k in range(1, 10)] + ["1.0"]   # decile groups D1..D10 ("top" = D10)
data = {"t": series["time"].tolist(), "shares": {}, "levels": {}, "quantiles": {}}
for v in V:
    col = lambda stat, p: f"{v}_{stat}_" + ("top" if p == "1.0" else f"p{p[2]}0") + "_psid"
    data["shares"][v] = {p: clean(series[col("share", p)], 5) for p in P}
    data["levels"][v] = {p: clean(series[col("level", p)] / 1e12, 4) for p in P}
    data["quantiles"][v] = {p: clean(series[col("quantile", p)], 2) for p in P}

g = master.dropna(subset=["cop_share"])
full = g.groupby(["year", "quarter"]).size()
full = full[full == 1000].index                      # complete 10x10x10 grid
bivar = {"t": [], "ci": [], "cw": [], "iw": []}
pairs = {"ci": ("consumgrid", "incomegrid"), "cw": ("consumgrid", "wealthgrid"), "iw": ("incomegrid", "wealthgrid")}
for (y, q) in full:
    sub = g[(g.year == y) & (g.quarter == q)]
    bivar["t"].append(f"{y}-Q{q}")
    for k, (a, b) in pairs.items():
        m = sub.pivot_table(index=a, columns=b, values="cop_share", aggfunc="sum").values
        bivar[k].append(np.round(m, 4).tolist())

def js(obj):                                         # JS literal: missing values as NaN
    return json.dumps(obj, separators=(",", ":")).replace("null", "NaN")

s = open(HTML).read()
s, n1 = re.subn(r"const DATA = \{.*?\};\n", lambda _: f"const DATA = {js(data)};\n", s, count=1, flags=re.S)
assert n1 == 1
open(HTML, "w").write(s)
with open(os.path.join(ROOT, "data", "bivar.json"), "w") as f:   # loaded lazily by the joint-distribution tab
    json.dump(bivar, f, separators=(",", ":"))
print(f"DATA {data['t'][0]}..{data['t'][-1]} ({len(data['t'])} q); BIVAR {bivar['t'][0]}..{bivar['t'][-1]} ({len(bivar['t'])} q)")
