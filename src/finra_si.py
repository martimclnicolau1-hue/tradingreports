# -*- coding: utf-8 -*-
"""v12-B4: FINRA short interest consolidado (bi-mensal) — dSI + days-to-cover.

Fonte: api.finra.org/data/group/otcMarket/name/consolidatedShortInterest
(grátis, JSON, sem chave). Substitui o papel do shortPercentOfFloat do
yfinance (snapshot sem data — errata v12§7): aqui temos posição atual E
anterior + ADV da própria FINRA, com data de liquidação.

CAVEAT PIT declarado: o ficheiro é publicado ~T+8 dias úteis após o
settlement — em uso histórico, key na DATA DE PUBLICAÇÃO. Este módulo v1
serve o brief (contexto live); backfill histórico fica para o tribunal
futuro. CONTEXTO, zero peso.

Uso: .venv/bin/python -m src.finra_si   (noturno, após rescore)
"""
import numpy as np
import pandas as pd
import requests

URL = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
HEADERS = {"Accept": "application/json",
           "User-Agent": "EventCalendarResearch/1.0 (contacto: luis@nikufra.ai)"}


PART_URL = "https://api.finra.org/partitions/group/otcMarket/name/consolidatedShortInterest"


def latest_settlement():
    r = requests.get(PART_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    parts = [p["partitions"][0] for p in r.json()["availablePartitions"]]
    return max(parts)


def fetch_all(limit=5000, max_pages=12):
    """A API é particionada por settlementDate (sem filtro devolve 2020!) —
    descobre a partição mais recente e pagina só essa."""
    settle = latest_settlement()
    rows = []
    for page in range(max_pages):
        r = requests.post(URL, json={
            "limit": limit, "offset": page * limit,
            "compareFilters": [{"compareType": "EQUAL", "fieldName": "settlementDate",
                                "fieldValue": settle}]},
            headers={**HEADERS, "Content-Type": "application/json"}, timeout=60)
        r.raise_for_status()
        chunk = r.json()
        if not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < limit:
            break
    return pd.DataFrame(rows)


def main():
    df = fetch_all()
    sym_col = next((c for c in ["symbolCode", "issueSymbolIdentifier", "symbol"]
                    if c in df.columns), None)
    if sym_col is None:
        print(f"[WARN] finra_si: colunas inesperadas {list(df.columns)[:10]} — a abortar sem escrever")
        return
    df = df.rename(columns={sym_col: "ticker"})
    cur = pd.to_numeric(df.get("currentShortPositionQuantity"), errors="coerce")
    prev = pd.to_numeric(df.get("previousShortPositionQuantity"), errors="coerce")
    adv = pd.to_numeric(df.get("averageDailyVolumeQuantity"), errors="coerce")
    df["dsi_pct"] = ((cur - prev) / prev.replace(0, np.nan)).round(4)
    df["days_to_cover"] = (cur / adv.replace(0, np.nan)).round(2)
    settle = next((c for c in df.columns if "settlement" in c.lower()), None)
    keep = df.groupby("ticker").tail(1).set_index("ticker")

    cand = pd.read_csv("output/candidatos.csv")
    cand["dsi_pct"] = cand.ticker.map(keep["dsi_pct"])
    cand["days_to_cover"] = cand.ticker.map(keep["days_to_cover"])
    cand.to_csv("output/candidatos.csv", index=False)
    ok = cand.dsi_pct.notna()
    top = cand[ok].nlargest(5, "days_to_cover")[["ticker", "days_to_cover", "dsi_pct"]]
    print(f"FINRA SI: {ok.sum()}/{len(cand)} candidatos cobertos"
          + (f" (settlement: {df[settle].max()})" if settle else ""))
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
