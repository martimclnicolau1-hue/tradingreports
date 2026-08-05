# -*- coding: utf-8 -*-
"""v5: universo automático — descobre TODOS os tickers US com earnings na janela.

Fonte primária: endpoint público de calendário da Nasdaq (sem key; dá data,
timing BMO/AMC e market cap). Fontes opcionais atrás de env keys: API Ninjas
(API_NINJAS_KEY) e EarningsAPI (EARNINGSAPI_KEY). yfinance continua a ser a
segunda fonte de validação em run.py (regra das 2 fontes).

Filtro de elegibilidade fixado na metodologia v5: market cap >= MIN_MCAP.
Degradação: qualquer fonte pode falhar; todas mortas -> run.py usa a lista
manual de fallback com aviso visível.
"""
import os
import re
import time
from datetime import timedelta

import requests

from . import config
from .fetch import _load_cache, _save_cache

BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json",
}


def _parse_mcap(s):
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", str(s))
    return float(digits) if digits else None


def fetch_calendar_nasdaq(day):
    """Um dia de calendário Nasdaq. Devolve lista de dicts ou None."""
    url = f"https://api.nasdaq.com/api/calendar/earnings?date={day.isoformat()}"
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
        r.raise_for_status()
        rows = ((r.json().get("data") or {}).get("rows")) or []
        out = []
        for row in rows:
            t = (row.get("time") or "").lower()
            timing = "BMO" if "pre-market" in t else ("AMC" if "after-hours" in t else "?")
            out.append({
                "ticker": (row.get("symbol") or "").upper().strip(),
                "date": day.isoformat(),
                "timing": timing,
                "mcap": _parse_mcap(row.get("marketCap")),
                "eps_forecast": row.get("epsForecast"),
                "n_estimates": row.get("noOfEsts"),
                "source": "nasdaq",
            })
        return out
    except Exception as e:
        print(f"  [WARN] Nasdaq calendar {day}: {e}")
        return None


def fetch_calendar_apininjas(start, end):
    key = os.environ.get("API_NINJAS_KEY")
    if not key:
        return None
    try:
        r = requests.get("https://api.api-ninjas.com/v1/upcomingearnings",
                         headers={"X-Api-Key": key}, timeout=20)
        r.raise_for_status()
        out = []
        for row in r.json():
            d = row.get("date") or row.get("earnings_date")
            if d and start.isoformat() <= d <= end.isoformat():
                out.append({"ticker": (row.get("ticker") or "").upper(), "date": d,
                            "timing": "?", "mcap": None, "source": "apininjas"})
        return out
    except Exception as e:
        print(f"  [WARN] API Ninjas: {e}")
        return None


def fetch_calendar_earningsapi(start, end):
    key = os.environ.get("EARNINGSAPI_KEY")
    if not key:
        return None
    out = []
    day = start
    try:
        while day <= end:
            r = requests.get("https://api.earningsapi.com/v1/calendar/earnings",
                             params={"date": day.isoformat()},
                             headers={"Authorization": f"Bearer {key}"}, timeout=20)
            if r.status_code == 200:
                for row in r.json() if isinstance(r.json(), list) else r.json().get("data", []):
                    out.append({"ticker": (row.get("symbol") or row.get("ticker") or "").upper(),
                                "date": day.isoformat(), "timing": "?", "mcap": None,
                                "source": "earningsapi"})
            time.sleep(1.0)
            day += timedelta(days=1)
        return out
    except Exception as e:
        print(f"  [WARN] EarningsAPI: {e}")
        return None


def build_universe(start, end):
    """Universo automático da janela. Devolve (dict ticker->meta, stats)."""
    cache_name = f"universe_{start.isoformat()}_{end.isoformat()}.json"
    cached = _load_cache(cache_name, max_age_hours=24)
    if cached is not None:
        return cached["tickers"], cached["stats"]

    raw = []
    sources_ok = []
    day = start
    nasdaq_failed = []  # v11: uma falha num dia deixou de abortar a janela toda
    while day <= end:
        if day.weekday() < 5:  # dias úteis
            rows = fetch_calendar_nasdaq(day)
            if rows is None:
                nasdaq_failed.append(day.isoformat())
            else:
                raw.extend(rows)
            time.sleep(config.REQUEST_SLEEP)
        day += timedelta(days=1)
    if not nasdaq_failed:
        sources_ok.append("nasdaq")
    elif raw:
        sources_ok.append(f"nasdaq(parcial — falhou: {', '.join(nasdaq_failed)})")
    for fn, name in [(fetch_calendar_apininjas, "apininjas"),
                     (fetch_calendar_earningsapi, "earningsapi")]:
        rows = fn(start, end)
        if rows:
            raw.extend(rows)
            sources_ok.append(name)

    tickers = {}
    n_filtered_mcap = 0
    for row in raw:
        tk = row["ticker"]
        if not tk or not tk.isascii():
            continue
        # filtro de elegibilidade fixo (metodologia v5): mcap conhecido < MIN_MCAP -> fora
        if row.get("mcap") is not None and row["mcap"] < config.MIN_MCAP:
            n_filtered_mcap += 1
            continue
        cur = tickers.setdefault(tk, {"date": row["date"], "timing": row["timing"],
                                      "mcap": row.get("mcap"), "sources": set()})
        cur["sources"].add(row["source"])
        if cur["timing"] == "?" and row["timing"] != "?":
            cur["timing"] = row["timing"]
        if cur.get("mcap") is None:
            cur["mcap"] = row.get("mcap")
    for meta in tickers.values():
        meta["sources"] = sorted(meta["sources"])

    stats = {
        "sources_ok": sources_ok,
        "raw_rows": len(raw),
        "n_tickers": len(tickers),
        "n_filtered_mcap": n_filtered_mcap,
        "min_mcap": config.MIN_MCAP,
        "nasdaq_failed_days": nasdaq_failed,
    }
    _save_cache(cache_name, {"tickers": tickers, "stats": stats})
    print(f"Universo automático: {len(tickers)} tickers elegíveis "
          f"(fontes: {sources_ok or 'NENHUMA'}; {n_filtered_mcap} filtrados por mcap)")
    return tickers, stats
