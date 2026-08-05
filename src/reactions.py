# -*- coding: utf-8 -*-
"""v8: computação ÚNICA de reações a earnings (AMC/BMO close→close).

Consolidação da fórmula que existia duplicada em metrics/factor_study/
ev_engine — a paridade painel/candidatos fica garantida por construção.
"""
import pandas as pd


def event_reactions(edf, prices):
    """Para cada earnings passado devolve dicts (mais recente primeiro):
    {date, amc, i_before, i_after, reaction, surprise}. Dedupe por dia."""
    if edf is None or prices is None or edf.empty or len(prices) < 2:
        return []
    scol = next((c for c in edf.columns if "surprise" in c.lower()), None)
    idx = prices.index.tz_localize(None).normalize()
    closes = prices["Close"].values
    now = pd.Timestamp.utcnow().tz_localize(None)
    past = edf[edf["date"].dt.tz_localize(None) < now]
    out, seen = [], set()
    for _, r in past.iterrows():
        ts = r["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0
        day = pd.Timestamp(ts.date())
        pos = idx.searchsorted(day)
        b, a = (pos, pos + 1) if amc else (pos - 1, pos)
        key = str(day.date())
        if b < 0 or a >= len(closes) or key in seen:
            continue
        seen.add(key)
        out.append({
            "date": key, "amc": bool(amc), "i_before": int(b), "i_after": int(a),
            "reaction": float(closes[a] / closes[b] - 1),
            "surprise": float(r[scol]) if scol and pd.notna(r[scol]) else None,
        })
    return out
