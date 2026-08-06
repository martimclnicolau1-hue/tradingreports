# -*- coding: utf-8 -*-
"""v7: calcula hype_score (camada social ao vivo) para os candidatos com evento
nos próximos 3 dias. CONTEXTO — nunca entra no EV (metodologia v7).

Uso: .venv/bin/python -m src.hype_calc
"""
import json
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import altdata
from .factor_study import load_prices


def rel_volume_now(sym):
    pr = load_prices(sym)
    if pr is None or "Volume" not in pr or len(pr) < 65:
        return None
    v = pr["Volume"].astype(float).values
    v60 = np.nanmean(v[-65:-5]); v5 = np.nanmean(v[-5:])
    return float(v5 / v60) if v60 and v60 > 0 else None


def main():
    df = pd.read_csv("output/candidatos.csv")
    optclean = {}
    if os.path.exists("data/optclean.json"):
        optclean = json.load(open("data/optclean.json"))

    horizon = [(date.today() + timedelta(days=d)).isoformat()
               for d in range(0, getattr(config, "SCOPE_DAYS", 3) + 1)]
    scope = df.event_date.isin(horizon)
    print(f"Hype: a calcular para {scope.sum()} candidatos (eventos até T+3)")

    relvols, optvols, pcrs, wikis = [], [], [], []
    for _, r in df.iterrows():
        if not scope.loc[r.name]:
            relvols.append(np.nan); optvols.append(np.nan)
            pcrs.append(np.nan); wikis.append(np.nan)
            continue
        relvols.append(rel_volume_now(r.ticker) or np.nan)
        oc = optclean.get(r.ticker) or {}
        optvols.append(oc.get("opt_volume_front") or np.nan)
        pcrs.append(oc.get("put_call_vol_ratio") or np.nan)
        art = altdata.wiki_article_for(r.ticker)
        w = {}
        if art:
            w, _ = altdata.fetch_wiki_pageviews(art)
        wikis.append((w or {}).get("wiki_ratio") or np.nan)

    df["rel_volume_now"] = relvols
    df["opt_volume_front"] = optvols
    df["put_call_vol_ratio_now"] = pcrs
    df["wiki_ratio"] = wikis

    sub = df[scope].copy()
    hs = altdata.hype_score(sub)
    df["hype_score"] = np.nan
    if hs is not None:
        df.loc[sub.index, "hype_score"] = hs.values
    df.to_csv("output/candidatos.csv", index=False)
    top = df[scope & df.hype_score.notna()].sort_values("hype_score", ascending=False)
    cols = [c for c in ["ticker", "event_date", "hype_score", "reddit_mentions",
                        "wiki_ratio", "rel_volume_now"] if c in top.columns]
    print(top[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
