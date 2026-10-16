"""Rebuild the Data Explorer's embedded data (const DATA in index.html; data/bivar.json)
from the published data products, so the charts match the downloads.

    python3 tools/build_explorer_data.py            # reads data/dd_series.csv, data/dd_master.csv

DATA        univariate, PSID view, decile groups D1..D10: share of total, group total (trillions of
            2019Q4 USD) and mean per household (2019Q4 USD; the `quantile_*` columns), 1962-Q3 onward.
BIVAR_DATA  bivariate: 10x10 population shares of decile cells. C x I and C x W: PSID view, the
            synthetic-microdata copula grid (dd_master.csv, cop_share) summed over the third variable,
            quarters with PSID consumption (1999-Q2 on). I x W: SCF view, the income x wealth copula
            cells of SCF_functional_data.csv (ciw_1jk), 1962-Q3 on. Each pair has its own quarters
            (t_ci, t_cw, t_iw).
"""
import json, os, re
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
series = pd.read_csv(os.path.join(ROOT, "data", "dd_series.csv"))
master = pd.read_csv(os.path.join(ROOT, "data", "dd_master.csv"))
# SCF copula cells are not hosted on the site; read them from DD_data (local checkout or GitHub)
SCF_FD = os.environ.get("SCF_FD", "https://raw.githubusercontent.com/LuisCald/DD_data/main/data/SCF_functional_data.csv")

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

bivar = {"t_ci": [], "t_cw": [], "t_iw": [], "ci": [], "cw": [], "iw": []}
for (y, q), sub in master.groupby(["year", "quarter"]):
    if sub.consum.isna().all():                      # no PSID consumption before 1999-Q2
        continue
    for k, (a, b) in {"ci": ("consumgrid", "incomegrid"), "cw": ("consumgrid", "wealthgrid")}.items():
        m = sub.pivot_table(index=a, columns=b, values="cop_share", aggfunc="sum").values
        bivar["t_" + k].append(f"{y}-Q{q}")
        bivar[k].append(np.round(m, 4).tolist())

def _cell(col):                                      # ciw_1jk -> (income j, wealth k); j, k in 1..10
    r = col[len("ciw_1"):].split(".")[0]
    if len(r) == 4:
        return (10, 10)
    return (int(r[0]), int(r[1])) if len(r) == 2 else ((10, int(r[2])) if r.startswith("10") else (int(r[0]), 10))
scf = pd.read_csv(SCF_FD)
cells = {c: _cell(c) for c in scf.columns if c.startswith("ciw_1") and scf[c].notna().any()}
assert len(cells) == 100 and len(set(cells.values())) == 100
for _, row in scf.iterrows():
    m = np.full((10, 10), np.nan)
    for c, (j, k) in cells.items():
        m[j - 1, k - 1] = row[c]
    if np.isnan(m).any():
        continue
    bivar["t_iw"].append(row.time)
    bivar["iw"].append(np.round(m, 4).tolist())

def js(obj):                                         # JS literal: missing values as NaN
    return json.dumps(obj, separators=(",", ":")).replace("null", "NaN")

s = open(HTML).read()
s, n1 = re.subn(r"const DATA = \{.*?\};\n", lambda _: f"const DATA = {js(data)};\n", s, count=1, flags=re.S)
assert n1 == 1
open(HTML, "w").write(s)
with open(os.path.join(ROOT, "data", "bivar.json"), "w") as f:   # loaded lazily by the joint-distribution tab
    json.dump(bivar, f, separators=(",", ":"))
print(f"DATA {data['t'][0]}..{data['t'][-1]} ({len(data['t'])} q); " + "; ".join(
    f"{k} {bivar['t_' + k][0]}..{bivar['t_' + k][-1]} ({len(bivar['t_' + k])} q)" for k in ("ci", "cw", "iw")))
