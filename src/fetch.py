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


def fetch_earnings_dates(symbol, limit=100, force=False):
    """Datas de earnings passadas e futuras via yfinance. Devolve DataFrame ou None.
    v10: limit=100 (máximo yfinance; 30 bucketizava para 50); force ignora a cache."""
    cached = None if force else _load_cache(f"earnings_{symbol}.json")
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


def fetch_prices(symbol, period="10y", force=False):
    """Histórico diário OHLCV. Devolve (DataFrame, verified).
    v10: period=10y default; force ignora a cache.
    v14: refresh INCREMENTAL — cache velha ganha só as barras novas (append),
    em vez de re-descarregar 10 anos por ticker (mata as 4h do runner cloud).
    Qualquer falha no incremento degrada para o refetch completo antigo."""
    path = _cache_path(f"prices_{symbol}.csv")
    if os.path.exists(path) and not force:
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        old = pd.read_csv(path, index_col=0)
        old.index = pd.to_datetime(old.index, utc=True, errors="coerce")
        old = old[old.index.notna() & old["Close"].notna()]
        if age_h < 24:
            return old, True
        # v14: incremental — buscar só desde a última barra
        try:
            if len(old) >= 200:
                start = (old.index.max() - pd.Timedelta(days=7)).date().isoformat()
                t = get_ticker(symbol)
                nov = t.history(start=start, auto_adjust=True)
                time.sleep(config.REQUEST_SLEEP / 2)
                if nov is not None and not nov.empty:
                    nov.index = pd.to_datetime(nov.index, utc=True, errors="coerce")
                    df = pd.concat([old[old.index < nov.index.min()], nov])
                    df = df[~df.index.duplicated(keep="last")].sort_index()
                    df.to_csv(path)
                    return df[df["Close"].notna()], True
        except Exception as e:
            print(f"  [WARN] prices incremental {symbol}: {e} — full refetch")
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
    """Demonstrações anuais/trimestrais para os scores forenses.
    v13: cache de 72h (era o ÚNICO fetch sem cache — com o universo sem piso
    tornava-se o custo dominante: 1.703 idas à rede por noite; dados
    trimestrais toleram 3 dias de idade — custo, não critério)."""
    import pickle
    path = _cache_path(f"fin_{symbol}.pkl")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < 72 * 3600:
        try:
            with open(path, "rb") as f:
                out = pickle.load(f)
            ok = any(df is not None and not df.empty for df in out.values())
            return out, ok
        except Exception:
            pass  # cache corrompida → refetch
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
        if ok:
            try:
                with open(path, "wb") as f:
                    pickle.dump(out, f)
            except Exception:
                pass
        return out, ok
    except Exception as e:
        print(f"  [WARN] financials {symbol}: {e}")
        return {}, False
