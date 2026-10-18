"""Build data/explorer_bands.json: 95% posterior bands for the Data Explorer (loaded only when a reader turns
the band on, so the page itself loads no more data).

    python3 tools/build_explorer_bands.py <explorer_bands.csv>

The CSV comes from DD_replication's code/julia/export_explorer_bands.jl: 200 posterior draws of the October
2026 estimates, each with a drawn path of the factors (parameter and factor uncertainty), PSID view; 2.5th and
97.5th percentiles of the decile groups' share, total and mean, and of bottom 50 / next 40 / top 10 computed per
draw (not by summing decile bands). Quarters that are blank in the published series stay blank here.
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bands = pd.read_csv(sys.argv[1])
series = pd.read_csv(os.path.join(ROOT, "data", "dd_series.csv"))
T = series["time"].tolist()
DEC = [f"0.{k}" for k in range(1, 10)] + ["1.0"]
GRP = {"g0": ("bottom50", DEC[:5]), "g1": ("next40", DEC[5:9]), "g2": ("top10", DEC[9:])}
COL = {"shares": "share", "levels": "level", "quantiles": "quantile"}
ND = {"shares": 5, "levels": 4, "quantiles": 2}

def pub_mask(var, metric, d):
    c = f"{var}_{COL[metric]}_" + ("top" if d == "1.0" else f"p{d[2]}0") + "_psid"
    return series[c].notna().to_numpy()

out = {"t": T, "lo": {}, "hi": {}}
for metric in COL:
    for side in ("lo", "hi"):
        out[side][metric] = {}
    for var in ("consum", "income", "wealth"):
        for side in ("lo", "hi"):
            out[side][metric][var] = {}
        sub = bands[(bands.stat == metric) & (bands["var"] == var)]
        keys = [(d, d, [d]) for d in DEC] + [(k, g, ds) for k, (g, ds) in GRP.items()]
        for key, group, members in keys:
            s = sub[sub.group == group].set_index("time").reindex(T)
            mask = np.logical_and.reduce([pub_mask(var, metric, d) for d in members])
            scale = 1.0   # levels are already in trillions, as in DATA
            for side, col in (("lo", "p025"), ("hi", "p975")):
                v = s[col].to_numpy() * scale
                out[side][metric][var][key] = [None if (not m or not np.isfinite(x)) else round(float(x), ND[metric]) for x, m in zip(v, mask)]

path = os.path.join(ROOT, "data", "explorer_bands.json")
with open(path, "w") as f:
    json.dump(out, f, separators=(",", ":"))
print(f"wrote {path}: {os.path.getsize(path) / 1024:.0f} kB")
