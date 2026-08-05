# -*- coding: utf-8 -*-
"""Camada de dados: yfinance + SEC EDGAR, com cache em disco.

Princípio: cada função devolve dados crus + um campo `verified` que indica
se a informação veio de fonte ao vivo (True) ou falhou/ficou em cache velha
(False). O relatório propaga sempre este estado — nada é apresentado como
facto sem origem.
"""
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd

from . import config

os.makedirs(config.CACHE_DIR, exist_ok=True)


def _cache_path(name):
    return os.path.join(config.CACHE_DIR, name)


def _save_cache(name, obj):
    with open(_cache_path(name), "w") as f:
        json.dump({"fetched_at": datetime.now(timezone.utc).isoformat(), "data": obj}, f)


def _load_cache(name, max_age_hours=24):
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        payload = json.load(f)
    age = datetime.now(timezone.utc) - datetime.fromisoformat(payload["fetched_at"])
    if age.total_seconds() > max_age_hours * 3600:
        return None
    return payload["data"]


def get_ticker(symbol):
    import yfinance as yf
    return yf.Ticker(symbol)


def fetch_earnings_dates(symbol, limit=30):
    """Datas de earnings passadas e futuras via yfinance. Devolve DataFrame ou None."""
    cached = _load_cache(f"earnings_{symbol}.json")
    if cached is not None:
        df = pd.DataFrame(cached)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], utc=True)
        return df, True
    try:
        t = get_ticker(symbol)
        df = t.get_earnings_dates(limit=limit)
        time.sleep(config.REQUEST_SLEEP)
        if df is None or df.empty:
            return None, False
        out = df.reset_index()
        out.columns = [str(c).lower().replace(" ", "_") for c in out.columns]
        out = out.rename(columns={out.columns[0]: "date"})
        serializable = out.copy()
        serializable["date"] = serializable["date"].astype(str)
        _save_cache(f"earnings_{symbol}.json", serializable.to_dict(orient="records"))
        out["date"] = pd.to_datetime(out["date"], utc=True)
        return out, True
    except Exception as e:
        print(f"  [WARN] earnings dates {symbol}: {e}")
        return None, False


def fetch_prices(symbol, period="3y"):
    """Histórico diário OHLCV. Devolve (DataFrame, verified)."""
    path = _cache_path(f"prices_{symbol}.csv")
    if os.path.exists(path):
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        if age_h < 24:
            df = pd.read_csv(path, index_col=0)
            df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
            df = df[df.index.notna() & df["Close"].notna()]
            return df, True
    try:
        t = get_ticker(symbol)
        df = t.history(period=period, auto_adjust=True)
        time.sleep(config.REQUEST_SLEEP)
        if df is None or df.empty:
            return None, False
        df.to_csv(path)
        return df, True
    except Exception as e:
        print(f"  [WARN] prices {symbol}: {e}")
        return None, False


def fetch_info(symbol):
    """Snapshot fundamental do yfinance (.info). Devolve (dict, verified)."""
    cached = _load_cache(f"info_{symbol}.json")
    if cached is not None:
        return cached, True
    try:
        t = get_ticker(symbol)
        info = t.info or {}
        time.sleep(config.REQUEST_SLEEP)
        keep = {
            k: info.get(k)
            for k in [
                "shortName", "sector", "industry", "marketCap", "currentPrice",
                "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "fiftyDayAverage",
                "twoHundredDayAverage", "shortPercentOfFloat", "sharesShort",
                "shortRatio", "trailingPE", "forwardPE", "enterpriseToRevenue",
                "enterpriseToEbitda", "totalCash", "totalDebt", "freeCashflow",
                "operatingCashflow", "revenueGrowth", "earningsGrowth",
                "grossMargins", "operatingMargins", "profitMargins", "beta",
                "heldPercentInsiders", "heldPercentInstitutions",
                "numberOfAnalystOpinions", "targetMeanPrice",
                "recommendationKey",
            ]
        }
        _save_cache(f"info_{symbol}.json", keep)
        return keep, True
    except Exception as e:
        print(f"  [WARN] info {symbol}: {e}")
        return {}, False


def fetch_implied_move(symbol):
    """Movimento implícito ≈ preço do ATM straddle / spot, na 1ª expiração
    pós-evento disponível. Devolve (dict, verified).

    Nota honesta: se a única expiração for mensal distante, o valor vem
    inflacionado por theta extra — o campo `expiry` permite julgar isso.
    """
    try:
        t = get_ticker(symbol)
        expiries = t.options
        time.sleep(config.REQUEST_SLEEP)
        if not expiries:
            return None, False
        expiry = expiries[0]
        chain = t.option_chain(expiry)
        time.sleep(config.REQUEST_SLEEP)
        spot = t.fast_info.get("last_price") or t.fast_info.get("lastPrice")
        if not spot:
            hist = t.history(period="5d")
            spot = float(hist["Close"].iloc[-1]) if not hist.empty else None
        if not spot:
            return None, False
        calls, puts = chain.calls.copy(), chain.puts.copy()
        calls["dist"] = (calls["strike"] - spot).abs()
        puts["dist"] = (puts["strike"] - spot).abs()
        atm_call = calls.sort_values("dist").iloc[0]
        atm_put = puts.sort_values("dist").iloc[0]

        def mid(row):
            bid, ask = row.get("bid", 0) or 0, row.get("ask", 0) or 0
            if bid > 0 and ask > 0:
                return (bid + ask) / 2
            return row.get("lastPrice", 0) or 0

        straddle = mid(atm_call) + mid(atm_put)
        if straddle <= 0:
            return None, False
        return {
            "spot": float(spot),
            "expiry": expiry,
            "atm_strike": float(atm_call["strike"]),
            "straddle_price": float(straddle),
            "implied_move_pct": float(straddle / spot),
        }, True
    except Exception as e:
        print(f"  [WARN] implied move {symbol}: {e}")
        return None, False


def fetch_financials(symbol):
    """Demonstrações anuais/trimestrais para os scores forenses."""
    try:
        t = get_ticker(symbol)
        out = {
            "income": t.income_stmt,
            "balance": t.balance_sheet,
            "cashflow": t.cashflow,
            "q_income": t.quarterly_income_stmt,
            "q_balance": t.quarterly_balance_sheet,
            "q_cashflow": t.quarterly_cashflow,
        }
        time.sleep(config.REQUEST_SLEEP)
        ok = any(df is not None and not df.empty for df in out.values())
        return out, ok
    except Exception as e:
        print(f"  [WARN] financials {symbol}: {e}")
        return {}, False
