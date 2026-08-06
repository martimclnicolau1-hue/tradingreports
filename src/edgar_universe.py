# -*- coding: utf-8 -*-
"""v15-P2: universo canónico de earnings 2019-2025 a partir do EDGAR.

SEED (correção 1 do utilizador): CIKs vêm dos form.idx TRIMESTRAIS
(todos os 8-K históricos, INCLUINDO empresas mortas) — nunca do
company_tickers.json (mapa atual = survivorship de CIK).

Por CIK: submissions.json (+páginas) → 8-K com item 2.02 em 2019-2025 →
acceptanceDateTime (convenção EDGAR: Eastern Time) → AMC (≥16:00) /
BMO (<09:30) / intermédio (excluído do universo estratégico, contado).
No mesmo passe: formerNames+tickers (matching P3) e marcadores de classe
de morte (DEFM14A, SC 14D9, 8-K 1.03 via items, Forms 25/15).

Rate: ≤8 req/s, UA declarado, backoff 403/429 (10 min), checkpoint/500
CIKs, resumável. Output: data/edgar/universe_2019_2025.csv.gz

Uso: .venv/bin/python -m src.edgar_universe
"""
import gzip
import json
import os
import subprocess
import time

import pandas as pd
import requests

from . import config

HDR = {"User-Agent": config.SEC_USER_AGENT, "Accept-Encoding": "gzip"}
IDX_DIR = "data/edgar/idx"
OUT = "data/edgar/universe_2019_2025.csv.gz"
CKPT = "data/edgar/crawl_checkpoint.json.gz"
YEARS = range(2019, 2026)
SLEEP = 0.13  # ~7,7 req/s — abaixo do teto de 10 da SEC


def _get(url, retries=5):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HDR, timeout=30)
        except requests.exceptions.RequestException as e:
            # v15.1: quedas de ligação (No route to host, timeouts) não matam o
            # crawl — backoff exponencial e retoma (o checkpoint protege o resto)
            wait = min(60 * (2 ** i), 900)
            print(f"  [rede] {type(e).__name__} — pausa {wait}s ({url[-40:]})")
            time.sleep(wait)
            continue
        if r.status_code in (403, 429):
            print(f"  [{r.status_code}] pausa 10 min ({url[-40:]})")
            time.sleep(600)
            continue
        if r.status_code == 404:
            return None
        if r.status_code >= 500:
            # v15.2e: 502/503 esporádicos do SEC matavam o crawl aos 10k CIKs —
            # tratam-se como queda de rede (backoff), nunca como erro fatal
            wait = min(60 * (2 ** i), 900)
            print(f"  [{r.status_code}] pausa {wait}s ({url[-40:]})")
            time.sleep(wait)
            continue
        r.raise_for_status()
        time.sleep(SLEEP)
        return r
    return None


def seed_ciks():
    """CIKs de TODOS os filers de 8-K 2019-2025 (form.idx — mortas incluídas)."""
    os.makedirs(IDX_DIR, exist_ok=True)
    ciks = {}
    for y in YEARS:
        for q in (1, 2, 3, 4):
            p = f"{IDX_DIR}/form_{y}Q{q}.idx"
            if not os.path.exists(p):
                r = _get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx")
                if r is None:
                    continue
                open(p, "wb").write(r.content)
            for line in open(p, encoding="latin-1"):
                if line.startswith("8-K ") or line.startswith("8-K/A "):
                    parts = line.split()
                    # formato fixo: Form | Company... | CIK | Date | Filename
                    for tok in reversed(parts):
                        if tok.isdigit() and len(tok) <= 10:
                            ciks[int(tok)] = None
                            break
    print(f"seed: {len(ciks)} CIKs com 8-K em 2019-2025 (mortas incluídas)")
    return sorted(ciks)


def _scan_filings(rec, cik, out, death):
    forms = rec.get("form", [])
    items = rec.get("items", [])
    acc = rec.get("acceptanceDateTime", [])
    dates = rec.get("filingDate", [])
    accn = rec.get("accessionNumber", [])
    for i, f in enumerate(forms):
        d = dates[i] if i < len(dates) else ""
        if f in ("DEFM14A", "SC 14D9"):
            death[cik]["ma"] += 1
        elif f in ("25", "25-NSE", "15-12B", "15-12G"):
            death[cik]["form25_15"] += 1
        if f != "8-K" or not d or not ("2019" <= d[:4] <= "2025"):
            continue
        it = items[i] if i < len(items) else ""
        if "1.03" in (it or ""):
            death[cik]["falencia"] += 1
        if "2.02" not in (it or ""):
            continue
        a = acc[i] if i < len(acc) else ""
        hh = int(a[11:13]) if len(a) >= 16 else -1
        mm = int(a[14:16]) if len(a) >= 16 else 0
        timing = ("AMC" if hh >= 16 else
                  "BMO" if (0 <= hh < 9 or (hh == 9 and mm < 30)) else "INTERMEDIO")
        out.append({"cik": cik, "event_filing_date": d, "acceptance": a,
                    "timing": timing, "accession": accn[i] if i < len(accn) else ""})


def _save_ckpt(done, rows, meta, death):
    """v15.2c: checkpoint gzipado (fica <100MB) e COMMITADO — o crawl
    sobrevive à morte do container, não só a quedas de rede (v15.1).
    Falhas de git nunca matam o crawl; falha de push é reportada."""
    with gzip.open(CKPT, "wt") as f:
        json.dump({"done": sorted(done), "rows": rows, "meta": meta,
                   "death": {str(k): v for k, v in death.items()}}, f)
    for cmd in (["git", "add", "-A", "data/edgar"],
                ["git", "-c", "user.name=edgar-crawl", "-c", "user.email=routine@cloud",
                 "commit", "-m", "edgar: checkpoint do crawl v15-P2"],
                ["git", "pull", "--rebase", "--autostash"],
                ["git", "push"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode != 0 and cmd[-1] == "push":
                print(f"  [aviso] push do checkpoint falhou: {(r.stderr or '').strip()[-200:]}")
        except Exception as e:
            print(f"  [aviso] git do checkpoint: {e}")


def crawl(ciks):
    ck = json.load(gzip.open(CKPT, "rt")) if os.path.exists(CKPT) else {"done": [], "rows": [], "meta": {}, "death": {}}
    done = set(ck["done"])
    death = {int(k): v for k, v in ck["death"].items()}
    rows, meta = ck["rows"], ck["meta"]
    todo = [c for c in ciks if c not in done]
    print(f"crawl: {len(todo)} CIKs por processar ({len(done)} feitos)")
    for n, cik in enumerate(todo, 1):
        death.setdefault(cik, {"ma": 0, "falencia": 0, "form25_15": 0})
        r = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if r is not None:
            try:
                d = r.json()
                meta[str(cik)] = {"name": d.get("name"),
                                  "tickers": d.get("tickers", []),
                                  "former": [f.get("name") for f in d.get("formerNames", [])]}
                _scan_filings(d.get("filings", {}).get("recent", {}), cik, rows, death)
                for extra in d.get("filings", {}).get("files", []):
                    if extra.get("filingTo", "0") >= "2019-01-01":
                        r2 = _get(f"https://data.sec.gov/submissions/{extra['name']}")
                        if r2 is not None:
                            _scan_filings(r2.json(), cik, rows, death)
            except Exception as e:
                print(f"  [WARN] CIK {cik}: {e}")
        done.add(cik)
        if n % 500 == 0:
            _save_ckpt(done, rows, meta, death)
            print(f"  checkpoint {n}/{len(todo)} — {len(rows)} eventos 2.02")
    _save_ckpt(done, rows, meta, death)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["name"] = df.cik.map(lambda c: (meta.get(str(c)) or {}).get("name"))
        df["tickers"] = df.cik.map(lambda c: "|".join((meta.get(str(c)) or {}).get("tickers", [])))
        df["former_names"] = df.cik.map(lambda c: "|".join((meta.get(str(c)) or {}).get("former", [])))
        for k in ("ma", "falencia", "form25_15"):
            df[f"death_{k}"] = df.cik.map(lambda c: death.get(c, {}).get(k, 0))
        with gzip.open(OUT, "wt") as f:
            df.to_csv(f, index=False)
    print(f"UNIVERSO CANÓNICO: {len(df)} eventos 8-K 2.02 (2019-2025) de "
          f"{df.cik.nunique() if not df.empty else 0} empresas | "
          f"AMC {int((df.timing=='AMC').sum())} · BMO {int((df.timing=='BMO').sum())} · "
          f"intermédio {int((df.timing=='INTERMEDIO').sum())} (excluído, contado) → {OUT}")


if __name__ == "__main__":
    os.makedirs("data/edgar", exist_ok=True)
    crawl(seed_ciks())
