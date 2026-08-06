# -*- coding: utf-8 -*-
"""v9: arquivo diário de chains de opções + sinais live CPIV e O/S.

Motivo (metodologia v9): não existe histórico gratuito de IV/volume de opções —
o backtest dos sinais de Atilgan (CPIV) e Johnson-So (O/S) só nasce do NOSSO
arquivo. Este módulo guarda um snapshot diário por candidato da janela e
escreve as colunas live no candidatos.csv (CONTEXTO, sem peso até validação).

Caveat registado (Muravyev-Pearson-Pollet 2022): ~2/3 da previsibilidade
destes sinais são borrow fees — interpretar com essa lente.

Uso: .venv/bin/python -m src.chain_archive
"""
import os
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config


def cpiv_and_os(sym):
    """CPIV (IV call − IV put, pares de strike ATM ±10%, ponderado por OI) e
    O/S (volume total de opções ×100 ÷ volume de ações). Snapshot arquivado."""
    import yfinance as yf
    try:
        t = yf.Ticker(sym)
        exps = t.options
        if not exps:
            return None
        chain = t.option_chain(exps[0])
        time.sleep(0.4)
        h = t.history(period="5d")
        h = h[h["Close"].notna()]
        if h.empty:
            return None
        spot = float(h["Close"].iloc[-1])
        stock_vol = float(h["Volume"].iloc[-1]) if "Volume" in h else np.nan

        c = chain.calls.copy()
        p = chain.puts.copy()
        for df_ in (c, p):
            df_["iv"] = df_["impliedVolatility"]
        band = (c.strike >= 0.9 * spot) & (c.strike <= 1.1 * spot)
        pairs = c[band].merge(p, on="strike", suffixes=("_c", "_p"))
        pairs = pairs[(pairs.impliedVolatility_c > 0.01) & (pairs.impliedVolatility_p > 0.01)]
        cpiv = None
        if len(pairs):
            w = (pairs.openInterest_c.fillna(0) + pairs.openInterest_p.fillna(0)).clip(lower=1)
            cpiv = float(np.average(pairs.impliedVolatility_c - pairs.impliedVolatility_p,
                                    weights=w))
        opt_vol = float(c.volume.fillna(0).sum() + p.volume.fillna(0).sum())
        os_ratio = float(opt_vol * 100 / stock_vol) if stock_vol and stock_vol > 0 else None

        # arquivo do snapshot completo (IV por strike) para backtests futuros
        os.makedirs("data/chains", exist_ok=True)
        snap = pd.concat([
            c.assign(side="C")[["side", "strike", "iv", "volume", "openInterest", "bid", "ask"]],
            p.assign(side="P")[["side", "strike", "iv", "volume", "openInterest", "bid", "ask"]],
        ])
        snap.insert(0, "spot", spot)
        snap.insert(0, "expiry", exps[0])
        snap.insert(0, "ticker", sym)
        path = f"data/chains/{date.today().isoformat()}.csv"
        snap.to_csv(path, mode="a", header=not os.path.exists(path), index=False)
        return {"cpiv": cpiv, "os_ratio": os_ratio}
    except Exception as e:
        print(f"  [WARN] chain {sym}: {e}")
        return None


def bundle_signals():
    """v12-B2: bundle de sinais do arquivo próprio (metodologia v12§5).
    smirk (Xing-Zhang-Zhao: IV put ~0,80-moneyness − IV ATM call; POSITIVO=
    proteção cara=bearish) computável já; implied_move_pctile (≥8 snapshots
    do ticker) e otm_call_oi_d5 (≥5 dias consecutivos) ativam com a maturação
    do arquivo — NaN até lá, nunca inventados. Persiste em
    data/chains/signals_YYYY-MM-DD.csv e nas colunas do candidatos.csv."""
    import glob
    snaps = sorted(glob.glob("data/chains/????-??-??.csv"))
    if not snaps:
        return
    hoje = snaps[-1][-14:-4]
    ch = pd.read_csv(snaps[-1])
    rows = []
    for sym, g in ch.groupby("ticker"):
        spot = float(g.spot.iloc[0])
        c = g[(g.side == "C") & (g.iv > 0.01)]
        p = g[(g.side == "P") & (g.iv > 0.01)]
        smirk = np.nan
        if len(c) and len(p):
            atm_c = c.iloc[(c.strike - spot).abs().argsort()].iloc[0]
            otm_p = p.iloc[(p.strike - 0.8 * spot).abs().argsort()].iloc[0]
            if abs(otm_p.strike - 0.8 * spot) <= 0.1 * spot:
                smirk = float(otm_p.iv - atm_c.iv)
        # ΔOI de calls OTM (delta proxy: strike 1,05-1,25×spot) vs 5 snapshots atrás
        oi_now = float(c[(c.strike >= 1.05 * spot) & (c.strike <= 1.25 * spot)]
                       .openInterest.fillna(0).sum())
        d_oi = np.nan
        if len(snaps) >= 6:
            old = pd.read_csv(snaps[-6])
            oc = old[(old.ticker == sym) & (old.side == "C")]
            if len(oc):
                sp0 = float(oc.spot.iloc[0])
                oi_old = float(oc[(oc.strike >= 1.05 * sp0) & (oc.strike <= 1.25 * sp0)]
                               .openInterest.fillna(0).sum())
                tot = float(oc.openInterest.fillna(0).sum())
                if tot > 0:
                    d_oi = (oi_now - oi_old) / tot
        rows.append({"asof": hoje, "ticker": sym, "smirk": smirk,
                     "otm_call_oi": oi_now, "otm_call_oi_d5": d_oi})
    sig = pd.DataFrame(rows)
    sig.to_csv(f"data/chains/signals_{hoje}.csv", index=False)
    df = pd.read_csv("output/candidatos.csv")
    m = sig.set_index("ticker")
    df["smirk"] = df.ticker.map(m.smirk)
    df["otm_call_oi_d5"] = df.ticker.map(m.otm_call_oi_d5)
    df.to_csv("output/candidatos.csv", index=False)
    ok = sig.smirk.notna().sum()
    print(f"Bundle: {ok} smirks calculados | ΔOI ativa com ≥6 snapshots "
          f"(temos {len(snaps)}) | signals_{hoje}.csv")


def main():
    df = pd.read_csv("output/candidatos.csv")
    horizon = [(date.today() + timedelta(days=d)).isoformat()
               for d in range(0, getattr(config, "SCOPE_DAYS", 3) + 1)]
    scope = df.event_date.isin(horizon)
    print(f"Arquivo de chains: {scope.sum()} candidatos (eventos até T+3)")
    cpivs, oss = [], []
    for _, r in df.iterrows():
        if not scope.loc[r.name]:
            cpivs.append(np.nan); oss.append(np.nan)
            continue
        res = cpiv_and_os(r.ticker) or {}
        cpivs.append(res.get("cpiv") if res.get("cpiv") is not None else np.nan)
        oss.append(res.get("os_ratio") if res.get("os_ratio") is not None else np.nan)
    df["cpiv"] = cpivs
    df["os_ratio"] = oss
    df.to_csv("output/candidatos.csv", index=False)
    top = df[scope & df.cpiv.notna()].sort_values("cpiv", ascending=False)
    print(top[["ticker", "event_date", "cpiv", "os_ratio"]].head(8).to_string(index=False))
    print("(CPIV>0 = calls caras → inclinação bullish documentada; CONTEXTO, não peso)")


if __name__ == "__main__":
    import sys
    if "--bundle-only" in sys.argv:
        bundle_signals()
    else:
        main()
        bundle_signals()
