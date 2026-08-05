# -*- coding: utf-8 -*-
"""Re-scoring v3 sobre o CSV existente (regra: metodologia.md v3)."""
import json, os
import numpy as np, pandas as pd

def clip01(x): return max(0.0, min(1.0, x))
def val(x, lo, hi):
    return 0.5 if x is None or (isinstance(x, float) and np.isnan(x)) else clip01((x-lo)/(hi-lo))

df = pd.read_csv("output/candidatos.csv")
d52s, moms, rsis = [], [], []
for t in df.ticker:
    d52 = mom = rsi_clean = None
    p = f"data/prices_{t}.csv"
    if os.path.exists(p):
        pr = pd.read_csv(p, index_col=0)
        c = pd.to_numeric(pr["Close"], errors="coerce").dropna()
        if len(c) > 260:
            d52 = float(c.iloc[-1]/c.tail(252).max()-1)
            mom = float(c.iloc[-1]/c.iloc[-61]-1)
            d = c.diff(); g = d.clip(lower=0).rolling(14).mean(); l = (-d.clip(upper=0)).rolling(14).mean()
            rsi_clean = float((100-100/(1+g/l)).iloc[-1])
        else:
            rsi_clean = None
    d52s.append(d52); moms.append(mom); rsis.append(rsi_clean if len(c) > 260 else None)
df["dist_52w_high"], df["mom60"] = d52s, moms
df["rsi14"] = rsis

def v3(r):
    direc = (0.40*val(r.dist_52w_high, -0.6, 0.0) + 0.27*val(r.rsi14, 30, 70)
             + 0.20*val(r.mom60, -0.3, 0.3) + 0.11*val(r.skew_pct, -0.4, 0.6)
             + 0.02*val(r.beat_rate_8q, 0.3, 0.9))
    edge = val(r.edge_ratio, 0.6, 1.5)
    return 100*(0.5*direc + 0.5*edge)

def veto(r):
    v = []
    if pd.notna(r.altman_z2) and r.altman_z2 < 1.1: v.append("Altman")
    if pd.notna(r.sloan_accruals) and r.sloan_accruals > 0.10: v.append("Accruals")
    if pd.notna(r.sbc_pct_revenue) and r.sbc_pct_revenue > 0.20: v.append("SBC")
    if pd.notna(r.beat_and_fell_rate) and r.beat_and_fell_rate > 0.50: v.append("Beat&Fell")
    return "; ".join(v)

df["score_v3"] = df.apply(v3, axis=1).round(1)
df["veto_v3"] = df.apply(veto, axis=1)
df.to_csv("output/candidatos.csv", index=False)

lines = ["", "## Ranking v3 (pós-estudo de fatores; ver metodologia v3) — topo por dia, vetados excluídos", "",
         "| Dia | 1º elegível | v3 | 2º elegível | v3 | Vetados no topo (motivo) |", "|---|---|---|---|---|---|"]
for day, g in df.dropna(subset=["event_date"]).groupby("event_date"):
    g = g.sort_values("score_v3", ascending=False)
    el = g[g.veto_v3 == ""]
    vets = "; ".join(f"{r.ticker} ({r.veto_v3})" for _, r in g[g.veto_v3 != ""].head(3).iterrows()) or "—"
    a = f"{el.iloc[0].ticker}" if len(el) else "—"; av = f"{el.iloc[0].score_v3}" if len(el) else "—"
    b = f"{el.iloc[1].ticker}" if len(el) > 1 else "—"; bv = f"{el.iloc[1].score_v3}" if len(el) > 1 else "—"
    lines.append(f"| {day} | **{a}** | {av} | {b} | {bv} | {vets} |")
with open("/dev/null", "a") as f:
    f.write("\n".join(lines) + "\n")
print(df.dropna(subset=["event_date"]).sort_values("score_v3", ascending=False)[
    ["ticker","event_date","score","score_v3","veto_v3","dist_52w_high","rsi14","edge_ratio"]].head(20).to_string(index=False))
