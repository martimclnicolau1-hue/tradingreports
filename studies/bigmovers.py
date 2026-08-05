# -*- coding: utf-8 -*-
"""Anatomia dos grandes movimentos de subida (y >= +10%) em dias de report."""
import json, os
import numpy as np, pandas as pd
from src.factor_study import build_panel

p = build_panel()
# junta market cap do snapshot (aproximação: mcap atual, não point-in-time — declarado)
mcaps = {}
for t in p.ticker.unique():
    f = f"data/info_{t}.json"
    if os.path.exists(f):
        mc = json.load(open(f))["data"].get("marketCap")
        if mc: mcaps[t] = np.log10(mc)
p["log_mcap"] = p.ticker.map(mcaps)
p["big_up"] = p.y >= 0.10
p["big_dn"] = p.y <= -0.10
base = p.big_up.mean()
print(f"Painel: {len(p)} eventos | P(subir >=10%) base = {base:.1%} | P(cair >=10%) = {p.big_dn.mean():.1%}\n")

def buckets(col, q=4, labels=None):
    d = p.dropna(subset=[col])
    d = d.assign(b=pd.qcut(d[col], q, duplicates="drop"))
    g = d.groupby("b", observed=True).agg(n=("y","size"), p_big_up=("big_up","mean"),
                                          p_big_dn=("big_dn","mean"), mean_y=("y","mean"))
    print(f"--- {col} (quartis, do mais baixo ao mais alto) ---")
    print((g.assign(p_big_up=lambda x:(100*x.p_big_up).round(0), p_big_dn=lambda x:(100*x.p_big_dn).round(0),
                    mean_y=lambda x:(100*x.mean_y).round(1))).to_string())
    print()

for c in ["prior_avg_move", "dist_52w_high", "log_mcap", "prior_up_big_rate", "rsi14", "mom60"]:
    buckets(c)

print("=== MECANISMO: a surpresa de EPS no próprio print ===")
d = p.dropna(subset=["surprise_at_k"])
bins = [-np.inf, 0, 5, 15, np.inf]; lab = ["miss (<=0)", "beat 0-5%", "beat 5-15%", "beat >15%"]
d = d.assign(b=pd.cut(d.surprise_at_k, bins, labels=lab))
g = d.groupby("b", observed=True).agg(n=("y","size"), p_big_up=("big_up","mean"), mean_y=("y","mean"))
print((g.assign(p_big_up=lambda x:(100*x.p_big_up).round(0), mean_y=lambda x:(100*x.mean_y).round(1))).to_string())
up = d[d.big_up]
print(f"\nDos {len(up)} grandes movimentos de subida: {100*(up.surprise_at_k>0).mean():.0f}% tiveram beat de EPS")
print(f"Mas dos {len(d[d.surprise_at_k>0])} beats, só {100*d[d.surprise_at_k>0].big_up.mean():.0f}% deram subida >=10%")
miss, beat = d[d.surprise_at_k<=0].y, d[d.surprise_at_k>0].y
print(f"Assimetria: reação média a miss = {100*miss.mean():.1f}% | a beat = {100*beat.mean():.1f}%")
