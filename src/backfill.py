# -*- coding: utf-8 -*-
"""v10: backfill único da cache — 10 anos de preços + earnings a limit=100.

Motivo (metodologia v10): o painel estava limitado a 21 meses porque
fetch_prices usava period=3y (e o refresh reescreve o CSV); a cache de
earnings estava capada a 50 registos (limit=30 bucketiza para 50).

Resumável: data/backfill_done.txt regista cada ticker cujo refetch de PREÇOS
(o dado crítico — 50 earnings ≈ 12 anos, já cobrem a janela 10y) teve sucesso;
re-correr o módulo salta os feitos e reprocessa só as falhas.

Uso: .venv/bin/python -m src.backfill
"""
import glob
import json
import os

from . import fetch

DONE_FILE = "data/backfill_done.txt"


def universe():
    syms = set()
    for pat, pre, suf in [("data/earnings_*.json", "data/earnings_", ".json"),
                          ("data/prices_*.csv", "data/prices_", ".csv")]:
        for p in glob.glob(pat):
            syms.add(p[len(pre):-len(suf)])
    return sorted(s for s in syms if s and not s.startswith("^"))


def needs_earnings_refetch(sym):
    path = f"data/earnings_{sym}.json"
    if not os.path.exists(path):
        return True
    try:
        with open(path) as f:
            return len(json.load(f)["data"]) >= 50  # capado no bucket antigo
    except Exception:
        return True


def main():
    done = set()
    if os.path.exists(DONE_FILE):
        done = set(open(DONE_FILE).read().split())
    syms = [s for s in universe() if s not in done]
    print(f"Backfill: {len(syms)} tickers por processar ({len(done)} já feitos)", flush=True)
    partial = []
    for i, sym in enumerate(syms, 1):
        _, ok_p = fetch.fetch_prices(sym, force=True)
        ok_e = True
        if needs_earnings_refetch(sym):
            _, ok_e = fetch.fetch_earnings_dates(sym, force=True)
        if ok_p:  # earnings a falhar não bloqueia: o ficheiro antigo mantém-se
            with open(DONE_FILE, "a") as f:
                f.write(sym + "\n")
        if not (ok_p and ok_e):
            partial.append(sym)
        print(f"[{i}/{len(syms)}] {sym}: {'OK' if ok_p and ok_e else f'parcial(p={ok_p},e={ok_e})'}",
              flush=True)
    print(f"Backfill terminado. Falhas/parciais: {len(partial)}"
          + (f" — {' '.join(partial[:30])}" if partial else ""), flush=True)


if __name__ == "__main__":
    main()
