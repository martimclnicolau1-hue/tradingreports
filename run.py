# -*- coding: utf-8 -*-
"""Pipeline completo num comando:  python run.py

Para cada ticker do universo: valida data de earnings na janela, calcula
reações históricas, movimento implícito, técnica, forense e o score
pré-registado; depois gera output/candidatos.csv + output/calendario.md
e corre o sanity-backtest walk-forward.
"""
import sys
from datetime import timedelta

import pandas as pd

from src import altdata, config, fetch, metrics, report, simulate, universe


def main():
    rows = []
    ctx = {}
    reactions_by_ticker = {}
    ws = pd.Timestamp(config.WINDOW_START)
    we = pd.Timestamp(config.WINDOW_END) + timedelta(days=1)

    # v5: universo automático de mercado inteiro (fallback manual declarado)
    auto_meta, coverage = {}, None
    if getattr(config, "AUTO_UNIVERSE", False):
        auto_meta, coverage = universe.build_universe(config.WINDOW_START, config.WINDOW_END)
    if auto_meta:
        tickers = sorted(set(auto_meta) | {ev["ticker"] for ev in config.MANUAL_EVENTS})
    else:
        tickers = list(config.UNIVERSE_FALLBACK)
        print("[AVISO] Todas as fontes de calendário falharam — a usar lista manual de fallback.")
        coverage = {"sources_ok": [], "fallback": True, "n_tickers": len(tickers)}

    # dados alternativos globais (cacheados) — CONTEXTO, não score
    wsb, wsb_ok = altdata.fetch_wsb_sentiment()
    print(f"Alt-data: WSB={'OK' if wsb_ok else 'FALHOU'}")

    for i, tkr in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {tkr}")
        edf, _ = fetch.fetch_earnings_dates(tkr)
        event_date, timing, in_window, date_verified = None, "?", False, False
        if edf is not None and not edf.empty:
            fut = edf[(edf["date"].dt.tz_localize(None) >= ws) & (edf["date"].dt.tz_localize(None) < we)]
            if not fut.empty:
                ts = fut.iloc[0]["date"].tz_convert("America/New_York")
                event_date = str(ts.date())
                timing = "AMC" if (ts.hour >= 16 or ts.hour == 0) else "BMO"
                in_window = True
                # regra das 2 fontes: verificado se calendário externo concorda ±1 dia
                am = auto_meta.get(tkr)
                date_verified = bool(am and abs((pd.Timestamp(am["date"]) - pd.Timestamp(event_date)).days) <= 1) or not auto_meta
        # fonte única (calendário externo sem confirmação yfinance): manter com flag
        if not in_window and tkr in auto_meta:
            am = auto_meta[tkr]
            event_date, in_window, date_verified = am["date"], True, False
            timing = am.get("timing", "?")
        # eventos manuais (PDUFA etc.) também contam como estar na janela
        for ev in config.MANUAL_EVENTS:
            if ev["ticker"] == tkr and config.WINDOW_START <= ev["date"] <= config.WINDOW_END:
                in_window = True
                event_date = event_date or ev["date"].isoformat()
        if not in_window:
            print(f"    sem evento na janela — descartado")
            continue

        prices, _ = fetch.fetch_prices(tkr)
        info, _ = fetch.fetch_info(tkr)
        fin, fin_ok = fetch.fetch_financials(tkr)
        implied = None  # v6: opções só na passagem 2 (top-N)
        reactions = metrics.earnings_reactions(prices, edf)
        reactions_by_ticker[tkr] = reactions
        rstats = metrics.reaction_stats(reactions)
        forensics = metrics.forensic_scores(fin) if fin_ok else {}
        surprises = metrics.surprise_stats(edf, reactions)
        rev_accel = None  # v8: fonte incapaz (yfinance dá <6 trimestres) — removido do fluxo
        score, decomp = metrics.composite_score(info, forensics, rstats, implied,
                                                surprises, rev_accel)
        wsb_row = wsb.get(tkr, {}) if wsb_ok else {}
        monthly_flag = False

        ctx[tkr] = {"info": info, "forensics": forensics, "rstats": rstats,
                    "surprises": surprises, "rev_accel": rev_accel}
        rows.append({
            "ticker": tkr,
            "event_date": event_date,
            "timing": timing,
            "date_verified": date_verified,
            "score": round(score, 1),
            "fundamental_0_1": decomp["fundamental_0_1"],
            "quant_0_1": decomp["quant_0_1"],
            "edge_ratio": decomp["edge_ratio"],
            "pct_missing": decomp["pct_missing"],
            "avg_abs_move": rstats.get("avg_abs_move"),
            "skew_pct": rstats.get("skew_pct"),
            "up_big_ci95": rstats.get("up_big_ci95"),
            "implied_move_pct": implied.get("implied_move_pct") if implied else None,
            "monthly_expiry_flag": monthly_flag,
            "short_pct_float": info.get("shortPercentOfFloat"),
            "altman_z2": forensics.get("altman_z2"),
            "sloan_accruals": forensics.get("sloan_accruals"),
            "sbc_pct_revenue": forensics.get("sbc_pct_revenue"),
            "beat_rate_8q": surprises.get("beat_rate_8q"),
            "surprise_momentum": surprises.get("surprise_momentum"),
            "beat_and_fell_rate": surprises.get("beat_and_fell_rate"),
            "expectations_0_1": decomp.get("expectations_0_1"),
            # contexto (fora do score)
            "wsb_comments": wsb_row.get("wsb_comments"),
        })

    if not rows:
        print("Nenhum evento confirmado na janela. Verifica a rede/datas.")
        sys.exit(1)

    # v6 passagem 2: opções só para o top-N do pré-score + estudados + posições
    ranked = sorted(rows, key=lambda r: -(r["score"] or 0))
    enrich = {r["ticker"] for r in ranked[:getattr(config, "ENRICH_TOP_N", 100)]}
    enrich |= set(getattr(config, "ALWAYS_ENRICH", [])) | set(config.EXISTING_POSITIONS)
    print(f"\nPassagem 2 (opções): {len(enrich & {r['ticker'] for r in rows})} tickers")
    by_tkr = {r["ticker"]: r for r in rows}
    for j, tkr in enumerate(sorted(enrich & set(by_tkr)), 1):
        r = by_tkr[tkr]
        implied, _ = fetch.fetch_implied_move(tkr)
        if not implied:
            continue
        c = ctx[tkr]
        score, decomp = metrics.composite_score(c["info"], c["forensics"], c["rstats"],
                                                implied, c["surprises"], c["rev_accel"])
        monthly_flag = False
        if r["event_date"]:
            days_to_exp = (pd.Timestamp(implied["expiry"]) - pd.Timestamp(r["event_date"])).days
            monthly_flag = days_to_exp > 10
        r.update({"score": round(score, 1), "edge_ratio": decomp["edge_ratio"],
                  "implied_move_pct": implied.get("implied_move_pct"),
                  "monthly_expiry_flag": monthly_flag,
                  "pct_missing": decomp["pct_missing"]})

    df = report.build_csv(rows)
    wf = simulate.walk_forward_check(reactions_by_ticker)
    path = report.build_calendar_md(rows, wf, coverage=coverage)
    print(f"\nOK: {len(df)} candidatos -> output/candidatos.csv, {path}")
    print("Lembrete: isto é informação, não aconselhamento. Confirma datas no IR de cada empresa.")


if __name__ == "__main__":
    main()
