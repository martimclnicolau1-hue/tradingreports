# -*- coding: utf-8 -*-
"""Teste empírico de 2 algoritmos de earnings-trading nos nossos dados:
A) Continuação intradiária pós-gap (entrar na abertura APÓS o print)
B) Autocorrelação de surpresas (sandbagging: blowouts em série?)
"""
import glob, json
import numpy as np, pandas as pd
from src.factor_study import load_earnings, load_prices

rows = []
for p in glob.glob("data/prices_*.csv"):
    sym = p.split("prices_")[1][:-4]
    edf, prices = load_earnings(sym), load_prices(sym)
    if edf is None or prices is None or len(prices) < 100: continue
    scol = next((c for c in edf.columns if "surprise" in c.lower()), None)
    idx = prices.index.tz_localize(None).normalize()
    o, c = prices["Open"].values, prices["Close"].values
    now = pd.Timestamp.utcnow().tz_localize(None)
    past = edf[edf["date"].dt.tz_localize(None) < now].reset_index(drop=True)
    surps = []
    for _, r in past.iterrows():
        ts = r["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0
        day = pd.Timestamp(ts.date()); pos = idx.searchsorted(day)
        b, a = (pos, pos+1) if amc else (pos-1, pos)
        s = float(r[scol]) if scol and pd.notna(r[scol]) else None
        prior4 = [x for x in surps[-4:] if x is not None]
        surps.append(s)
        if b < 1 or a >= len(c): continue
        gap = o[a]/c[b]-1
        intraday = c[a]/o[a]-1
        d3 = c[a+2]/c[a]-1 if a+2 < len(c) else None
        rows.append({"ticker": sym, "gap": gap, "intraday": intraday, "d3_from_close": d3,
                     "surprise": s, "prior_mean_surprise": np.mean(prior4) if len(prior4) >= 3 else None})
df = pd.DataFrame(rows)
print(f"Eventos com OHLC: {len(df)}\n")

print("=== A) CONTINUAÇÃO INTRADIÁRIA (comprar na ABERTURA pós-print) ===")
for lo, hi, lbl in [(0.05, np.inf, "gap-up >5%"), (0.10, np.inf, "gap-up >10%"),
                    (-np.inf, -0.05, "gap-down <-5%"), (-0.05, 0.05, "gap pequeno ±5%")]:
    d = df[(df.gap > lo) & (df.gap <= hi)] if hi != np.inf else df[df.gap > lo]
    if lo == -np.inf: d = df[df.gap < hi]
    if len(d) < 10: continue
    ir = d.intraday
    t = ir.mean()/(ir.std()/np.sqrt(len(ir)))
    print(f"  {lbl:18s} n={len(d):3d} | open->close médio: {100*ir.mean():+.2f}% "
          f"(mediana {100*ir.median():+.2f}%) | %positivo: {100*(ir>0).mean():.0f}% | t={t:.2f}")
d = df[(df.gap > 0.05) & df.surprise.notna() & (df.surprise > 15)]
if len(d) >= 10:
    ir = d.intraday; t = ir.mean()/(ir.std()/np.sqrt(len(ir)))
    print(f"  gap>5% E blowout>15% n={len(d):3d} | open->close: {100*ir.mean():+.2f}% | %pos: {100*(ir>0).mean():.0f}% | t={t:.2f}")

print("\n=== B) AUTOCORRELAÇÃO DE SURPRESAS (sandbagging) ===")
d = df.dropna(subset=["surprise", "prior_mean_surprise"])
r = d.prior_mean_surprise.rank().corr(d.surprise.rank())
n = len(d); t = r*np.sqrt((n-2)/(1-r**2))
print(f"  prior_mean_surprise -> surprise_atual: n={n} spearman={r:.3f} t={t:.2f}")
d["blowout"] = d.surprise > 15
g = d.assign(b=pd.qcut(d.prior_mean_surprise, 4, duplicates="drop")).groupby("b", observed=True)
print("  P(blowout>15%) por quartil de surpresa média anterior:")
print((100*g.blowout.mean()).round(0).to_string())
# e o elo que interessa: prior surprise -> REACAO (já vimos beat_rate=0; e a magnitude?)
d2 = df.dropna(subset=["prior_mean_surprise"])
d2["y"] = d2.gap + d2.intraday + d2.gap*d2.intraday
r2 = d2.prior_mean_surprise.rank().corr(d2.y.rank()); n2 = len(d2)
t2 = r2*np.sqrt((n2-2)/(1-r2**2))
print(f"  prior_mean_surprise -> reação de preço: n={n2} spearman={r2:.3f} t={t2:.2f}")
