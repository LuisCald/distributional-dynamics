# Builds og.png (1200x630 social preview) from data/dd_series.csv: SCF view, top-10% vs bottom-50% wealth shares.
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
repo = "/Users/lc/code/distributional-dynamics"
df = pd.read_csv(f"{repo}/data/dd_series.csv")
x = (df["year"] + (df["quarter"] - 1) / 4).to_numpy()
b50 = (df[[f"wealth_share_p{p}_scf" for p in (10,20,30,40,50)]].sum(axis=1, min_count=5) * 100).to_numpy()
t10 = (df["wealth_share_top_scf"] * 100).to_numpy()
import numpy as np; print(np.nanmin(b50), np.nanmax(b50), np.nanmin(t10), np.nanmax(t10))
BG, INK, FAINT, ACC, AMB = "#f6f4f0", "#1a1a2e", "#626276", "#1e3a5f", "#b45309"
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(0.06, 0.88, "Distributional Dynamics", fontsize=34, fontweight="bold", color=ACC, family="serif")
fig.text(0.06, 0.81, "Quarterly U.S. consumption, income & wealth distributions, 1962–2024",
         fontsize=17, color=INK, family="serif")
ax = fig.add_axes([0.07, 0.12, 0.86, 0.6], facecolor=BG)
ax.plot(x, t10, color=ACC, lw=3.2)
ax.plot(x, b50, color=AMB, lw=3.2)
ax.text(x[-1] + 0.8, t10[~np.isnan(t10)][-1], "Top 10%", color=ACC, fontsize=15, va="center", fontweight="bold")
ax.text(x[-1] + 0.8, b50[~np.isnan(b50)][-1], "Bottom 50%", color=AMB, fontsize=15, va="center", fontweight="bold")
ax.set_xlim(np.nanmin(x), np.nanmax(x) + 10)
ax.set_xticks(range(1970, 2021, 10)); ax.set_ylabel("Share of wealth (%)", color=FAINT, fontsize=13)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color("#d4cfc6")
ax.tick_params(colors=FAINT, labelsize=12)
ax.grid(axis="y", color="#d4cfc6", lw=0.6, alpha=0.7)
fig.text(0.94, 0.03, "distributionaldynamics.com", ha="right", fontsize=12, color=FAINT, family="monospace")
fig.savefig(f"{repo}/og.png", dpi=100, facecolor=BG)
