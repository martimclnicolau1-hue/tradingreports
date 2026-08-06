# -*- coding: utf-8 -*-
"""v12-A1: snapshot diário de estimativas de analistas (CAMINHO CRÍTICO).

O yfinance só dá o consenso ATUAL (sem data) — look-ahead garantido em
qualquer uso histórico. Este módulo constrói o painel point-in-time que
não existe: um ficheiro por dia com o consenso carimbado. É o pré-requisito
declarado (metodologia v12§5) do Revenue SUE e do NLP das calls (Fase C).

Formato: data/estimates/YYYY-MM-DD.csv.gz — 1 linha por ticker, colunas
achatadas (ee_*=earnings_estimate, re_*=revenue_estimate, et_*=eps_trend,
er_*=eps_revisions, pt_*=price targets). Idempotente por dia.

Uso: .venv/bin/python -m src.snapshot_estimates   (corre APÓS o brief noturno)
"""
import os
import time
from datetime import date

import pandas as pd

OUT_DIR = "data/estimates"
SLEEP = 0.4


def _flat(df, prefix):
    """DataFrame período×métrica → dict {prefix_período_métrica: valor}."""
    out = {}
    if df is None or getattr(df, "empty", True):
        return out
    for period, row in df.iterrows():
        for col, v in row.items():
            out[f"{prefix}_{period}_{col}"] = v
    return out


def snapshot_ticker(sym):
    from . import fetch
    t = fetch.get_ticker(sym)
    row = {"ticker": sym}
    try:
        row.update(_flat(t.get_earnings_estimate(), "ee"))
        row.update(_flat(t.get_revenue_estimate(), "re"))
        row.update(_flat(t.get_eps_trend(), "et"))
        row.update(_flat(t.get_eps_revisions(), "er"))
    except Exception as e:
        row["err_estimates"] = str(e)[:80]
    try:
        pt = t.analyst_price_targets or {}
        for k, v in pt.items():
            row[f"pt_{k}"] = v
    except Exception:
        pass
    return row


def main(force=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = f"{OUT_DIR}/{date.today().isoformat()}.csv.gz"
    if os.path.exists(path) and not force:
        print(f"snapshot de hoje já existe: {path}")
        return
    df = pd.read_csv("output/candidatos.csv")
    syms = sorted(df.ticker.dropna().unique())
    print(f"Snapshot de estimativas: {len(syms)} tickers → {path}", flush=True)
    rows = []
    for i, s in enumerate(syms, 1):
        rows.append(snapshot_ticker(s))
        time.sleep(SLEEP)
        if i % 100 == 0:
            print(f"  [{i}/{len(syms)}]", flush=True)
            # checkpoint parcial — um crash a meio não perde tudo
            pd.DataFrame(rows).to_csv(path, index=False, compression="gzip")
    out = pd.DataFrame(rows)
    out.insert(1, "asof", date.today().isoformat())
    out.to_csv(path, index=False, compression="gzip")
    ok = out.drop(columns=["ticker", "asof"]).notna().any(axis=1).sum()
    print(f"OK: {len(out)} tickers ({ok} com dados) → {path}", flush=True)


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)
