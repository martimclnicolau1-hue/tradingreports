# -*- coding: utf-8 -*-
"""v12-A4: FINRA daily short-sale volume — backfill 2018-08→hoje + features PIT.

Fonte: cdn.finra.org/equity/regsho/daily/CNMSshvol{YYYYMMDD}.txt (grátis,
publicado T+0 às ~18:00 ET; pipe-delimited: Date|Symbol|ShortVolume|
ShortExemptVolume|TotalVolume|Market). Histórico desde 2018-08-01.

Por que isto e não o shortPercentOfFloat: o campo do yfinance é um snapshot
SEM DATA (look-ahead em qualquer fit histórico — errata v12§7); os ficheiros
FINRA são datados → point-in-time por construção, backtestáveis JÁ.

Guarda só os tickers do nosso universo (data/earnings_*.json) em
data/finra/short_daily.csv.gz; resumável via data/finra/done.txt.

Uso: .venv/bin/python -m src.finra_short            # backfill/atualização
     .venv/bin/python -m src.finra_short --features # testa attach_features
"""
import glob
import gzip
import io
import os
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd
import requests

RAW_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"
DIR = "data/finra"
DATA = f"{DIR}/short_daily.csv.gz"
DONE = f"{DIR}/done.txt"
START = date(2018, 8, 1)
HEADERS = {"User-Agent": "EventCalendarResearch/1.0 (contacto: luis@nikufra.ai)"}


def _universe():
    syms = {p.split("earnings_")[1][:-5] for p in glob.glob("data/earnings_*.json")}
    return {s for s in syms if s and not s.startswith("^")}


def backfill():
    os.makedirs(DIR, exist_ok=True)
    done = set()
    if os.path.exists(DONE):
        done = set(open(DONE).read().split())
    uni = _universe()
    d, today = START, date.today()
    todo = []
    while d <= today:
        if d.weekday() < 5 and d.isoformat() not in done:
            todo.append(d)
        d += timedelta(days=1)
    print(f"FINRA backfill: {len(todo)} dias por descarregar ({len(done)} feitos), "
          f"universo {len(uni)} tickers", flush=True)
    buf, n_since = [], 0
    for i, d in enumerate(todo, 1):
        try:
            r = requests.get(RAW_URL.format(d=d.strftime("%Y%m%d")),
                             headers=HEADERS, timeout=30)
            if r.status_code == 404:      # feriado — marca feito e segue
                done.add(d.isoformat())
            else:
                r.raise_for_status()
                df = pd.read_csv(io.StringIO(r.text), sep="|")
                df = df[df.Symbol.isin(uni)][["Date", "Symbol", "ShortVolume", "TotalVolume"]]
                buf.append(df)
                done.add(d.isoformat())
        except Exception as e:
            print(f"  [WARN] {d}: {e}", flush=True)
        n_since += 1
        if n_since >= 50 or i == len(todo):   # flush a cada 50 dias — resumável
            if buf:
                mode, hdr = ("ab", False) if os.path.exists(DATA) else ("wb", True)
                with gzip.open(DATA, mode) as f:
                    pd.concat(buf).to_csv(io.TextIOWrapper(f), index=False, header=hdr)
                buf = []
            with open(DONE, "w") as f:
                f.write("\n".join(sorted(done)))
            print(f"  [{i}/{len(todo)}] checkpoint ({d})", flush=True)
            n_since = 0
        time.sleep(0.15)
    print("FINRA backfill terminado.", flush=True)


_RATIOS = None
def _load_ratios():
    """{symbol: Series(date→short_ratio)} com cache em memória."""
    global _RATIOS
    if _RATIOS is None:
        df = pd.read_csv(DATA)
        df["Date"] = pd.to_datetime(df.Date, format="%Y%m%d")
        df["ratio"] = df.ShortVolume / df.TotalVolume.replace(0, np.nan)
        df = df.dropna(subset=["ratio"]).sort_values("Date")
        _RATIOS = {s: g.set_index("Date")["ratio"] for s, g in df.groupby("Symbol")}
    return _RATIOS


def attach_features(panel):
    """Acrescenta short_ratio_z5 / short_ratio_z20 ao painel, PIT: usa APENAS
    dias estritamente ANTERIORES a event_date. NaN quando não há dados (o GBM
    imputa por mediana — comportamento padrão do harness)."""
    ratios = _load_ratios()
    z5s, z20s = [], []
    for sym, ev in zip(panel.ticker.values, pd.to_datetime(panel.event_date).values):
        s = ratios.get(sym)
        if s is None:
            z5s.append(np.nan); z20s.append(np.nan); continue
        h = s[s.index < ev]
        if len(h) < 60:
            z5s.append(np.nan); z20s.append(np.nan); continue
        base = h.tail(120)
        mu, sd = base.mean(), base.std()
        if not sd or np.isnan(sd) or sd == 0:
            z5s.append(np.nan); z20s.append(np.nan); continue
        z5s.append(float((h.tail(5).mean() - mu) / sd))
        z20s.append(float((h.tail(20).mean() - mu) / sd))
    panel["short_ratio_z5"] = z5s
    panel["short_ratio_z20"] = z20s
    return panel


if __name__ == "__main__":
    import sys
    if "--features" in sys.argv:
        p = pd.read_csv("output/factor_panel.csv")
        p = attach_features(p)
        print(p[["short_ratio_z5", "short_ratio_z20"]].describe())
        print("cobertura:", f"{p.short_ratio_z5.notna().mean():.1%}")
    else:
        backfill()
