# -*- coding: utf-8 -*-
"""Dados alternativos GRATUITOS: trades do Congresso + sentimento social.

REGRA METODOLÓGICA (ver metodologia.md v2): estes dados são CONTEXTO, não
inputs do score. Não há evidência de poder preditivo fiável a 1–2 dias;
servem para flags de crowding e para o utilizador julgar o posicionamento.

Fontes vivas (v8, 2026-08-05): Tradestie WSB, ApeWisdom, Wikipedia pageviews.
Removidas por mortas (403 permanente, ver metodologia v8): StockTwits, Senate
Stock Watcher, House Stock Watcher. X/Twitter API é paga — proxy = Reddit.
Cada função degrada para (None/{}, False) se a fonte falhar — nunca inventa.
"""
import time

import requests

from . import config
from .fetch import _load_cache, _save_cache

HEADERS = {"User-Agent": "Mozilla/5.0 (research pipeline; contacto no config)"}

def fetch_wsb_sentiment(max_age_hours=6):
    """Top ~50 tickers do r/wallstreetbets via Tradestie (sem key).
    Devolve (dict ticker->{comments, sentiment}, verified)."""
    cached = _load_cache("wsb_top.json", max_age_hours)
    if cached is not None:
        return cached, True
    try:
        r = requests.get("https://tradestie.com/api/v1/apps/reddit",
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        out = {row["ticker"]: {"wsb_comments": row.get("no_of_comments"),
                               "wsb_sentiment": row.get("sentiment")}
               for row in r.json()}
        _save_cache("wsb_top.json", out)
        return out, True
    except Exception as e:
        print(f"  [WARN] Tradestie WSB: {e}")
        return {}, False


# ---------------------------------------------------------------------------
# v7: hype/atenção pública
# ---------------------------------------------------------------------------
def fetch_wiki_pageviews(article, max_age_hours=24):
    """Views da página Wikipedia: rácio 7d vs média 30d. (dict, verified)."""
    import datetime as dt
    key = f"wiki_{article.replace('/', '_')[:60]}.json"
    cached = _load_cache(key, max_age_hours)
    if cached is not None:
        return cached, True
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=30)
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
           f"en.wikipedia/all-access/user/{article}/daily/"
           f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}")
    try:
        r = requests.get(url, headers={"User-Agent": config.SEC_USER_AGENT}, timeout=20)
        time.sleep(0.3)
        r.raise_for_status()
        items = r.json().get("items", [])
        views = [it["views"] for it in items]
        if len(views) < 10:
            return {}, False
        avg30 = sum(views) / len(views)
        avg7 = sum(views[-7:]) / min(7, len(views))
        out = {"wiki_ratio": round(avg7 / avg30, 3) if avg30 > 0 else None,
               "wiki_avg7": int(avg7)}
        _save_cache(key, out)
        return out, True
    except Exception:
        return {}, False


def wiki_article_for(sym):
    """Best-effort: título Wikipedia a partir do shortName do info cache."""
    import json as _json
    import os as _os
    import re as _re
    path = f"data/info_{sym}.json"
    if not _os.path.exists(path):
        return None
    try:
        name = (_json.load(open(path)).get("data") or {}).get("shortName") or ""
    except Exception:
        return None
    name = _re.sub(r"[,.]|\b(Inc|Corp|Corporation|Ltd|PLC|Co|Holdings?|Group|SA|AG|NV)\b",
                   "", name, flags=_re.I).strip()
    return name.replace(" ", "_") if name else None


def hype_score(rows_df):
    """Composto 0-100 de z-scores (pesos iguais — metodologia v7) sobre o
    universo do dia: reddit_mentions, wsb_comments, wiki_ratio, opt_volume,
    rel_volume. CONTEXTO, nunca entra no EV."""
    import numpy as np
    comps = []
    for col in ["reddit_mentions", "wsb_comments", "wiki_ratio",
                "opt_volume_front", "rel_volume_now"]:
        if col in rows_df and rows_df[col].notna().sum() >= 5:
            x = rows_df[col].astype(float)
            z = (x - x.mean()) / (x.std() or 1.0)
            comps.append(z.clip(-3, 3))
    if not comps:
        return None
    z = sum(c.fillna(0) for c in comps) / len(comps)
    return (50 + 20 * z).clip(0, 100).round(0)
