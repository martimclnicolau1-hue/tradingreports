# -*- coding: utf-8 -*-
"""Gera output/candidatos.csv + output/calendario.md (pt-PT).

O calendário é FACTUAL: datas, estatísticas e estado de verificação.
Deliberadamente NÃO contém instruções de compra/venda nem tamanhos de
posição — isso é decisão do utilizador (ou de um profissional licenciado).
"""
import os
import pandas as pd

from . import config


def fmt_pct(x, nd=1):
    return "—" if x is None else f"{100*x:.{nd}f}%"


def build_csv(rows, path="output/candidatos.csv"):
    df = pd.DataFrame(rows).sort_values("score", ascending=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return df


def build_calendar_md(rows, wf_result, path="output/calendario.md", coverage=None):
    rows = sorted([r for r in rows if r.get("event_date")], key=lambda r: r["event_date"])
    by_day = {}
    for r in rows:
        by_day.setdefault(r["event_date"], []).append(r)

    lines = []
    a = lines.append
    a("# Calendário de catalisadores — janela "
      f"{config.WINDOW_START.isoformat()} a {config.WINDOW_END.isoformat()}")
    a("")
    a("> **Natureza deste documento**: informação factual e estatística para investigação. "
      "Não é aconselhamento financeiro personalizado, não contém recomendações de "
      "compra/venda nem dimensionamento de posições. Amostras de n≈12 têm intervalos "
      "de confiança largos; um scan multi-ticker gera padrões por acaso "
      "(comparações múltiplas). Datas AMC/BMO devem ser confirmadas no IR de cada empresa.")
    a("")
    a("## Overlay macro (confirmar em bls.gov / census.gov)")
    for ev in config.MACRO_EVENTS:
        a(f"- **{ev['date'].isoformat()}** — {ev['name']} ({ev['time_et']} ET / "
          f"{int(ev['time_et'][:2])+5}:{ev['time_et'][3:]} Lisboa) — fonte: {ev['source']}")
    a("")
    a("## Eventos não-earnings introduzidos manualmente (NÃO verificados pelo pipeline)")
    for ev in config.MANUAL_EVENTS:
        a(f"- **{ev['date'].isoformat()}** — {ev['ticker']}: {ev['name']} — "
          f"{'verificado' if ev['verified'] else '**NÃO VERIFICADO — confirmar na FDA/IR**'}")
    a("")
    a("## Dia a dia (earnings verificados via yfinance no momento da execução)")
    for day in sorted(by_day):
        a(f"\n### {day}")
        a("| Ticker | Timing | Score | Fund. | Beat 8Q | Beat&Fell | Mov. hist. | Implícito | Edge | Skew | IC95 (≥+10%) | Falta | Notas |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in sorted(by_day[day], key=lambda x: -(x.get("score") or 0)):
            ci = r.get("up_big_ci95")
            ci_s = f"{100*ci[0]:.0f}–{100*ci[1]:.0f}%" if ci else "—"
            notes = []
            if r["ticker"] in config.EXISTING_POSITIONS:
                notes.append(config.EXISTING_POSITIONS[r["ticker"]])
            if not r.get("date_verified"):
                notes.append("DATA NÃO CONFIRMADA")
            if r.get("monthly_expiry_flag"):
                notes.append("implícito inflacionado (expiração mensal)")
            az = r.get("altman_z2")
            if az is not None and az < 1.1:
                notes.append(f"RED FLAG Altman {az:.1f}")
            a(f"| {r['ticker']} | {r.get('timing','?')} | {r.get('score',0):.0f} "
              f"| {r.get('fundamental_0_1','—')} | {fmt_pct(r.get('beat_rate_8q'),0)} "
              f"| {fmt_pct(r.get('beat_and_fell_rate'),0)} "
              f"| {fmt_pct(r.get('avg_abs_move'))} | {fmt_pct(r.get('implied_move_pct'))} "
              f"| {r.get('edge_ratio') or '—'} | {fmt_pct(r.get('skew_pct'),0)} | {ci_s} "
              f"| {fmt_pct(r.get('pct_missing'),0)} | {'; '.join(notes) or '—'} |")
    a("")
    a("## Sanity-backtest da regra de seleção (walk-forward, sem lookahead)")
    if wf_result:
        a(f"- Seleções: {wf_result.get('selecionados')}")
        a(f"- Rejeições: {wf_result.get('rejeitados')}")
        a(f"- **Conclusão: {wf_result.get('conclusao', 'n/d')}**")
    a("")
    if coverage:
        a("## Cobertura do universo (v5)")
        if coverage.get("fallback"):
            a("- **AVISO: fontes de calendário automático falharam — scan feito com lista manual de fallback.**")
        else:
            a(f"- Fontes de calendário ativas: {', '.join(coverage.get('sources_ok', [])) or '—'}; "
              f"{coverage.get('n_tickers', '?')} tickers elegíveis descobertos "
              f"({coverage.get('n_filtered_mcap', '?')} filtrados por market cap < ${coverage.get('min_mcap', 0)/1e6:.0f}M).")
        a("")
    a("## Secção de honestidade (obrigatória)")
    a("- Todos os dados datam do momento em que correste `python run.py` — verifica o timestamp em `data/`.")
    a("- Campos '—' = indisponíveis na fonte gratuita; nunca foram estimados.")
    a("- Revisões de estimativas de analistas, whisper numbers e 13F recentes NÃO estão em fontes gratuitas fiáveis — em falta por design, não por esquecimento.")
    a("- O movimento implícito via straddle ATM em expiração mensal sobrestima o movimento do evento.")
    a("- Sentimento social (Reddit/Wikipedia) é CONTEXTO, não input do score. Fontes mortas removidas na v8: StockTwits, Senate/House Stock Watcher (403 permanentes). X/Twitter API é paga — proxy = Reddit + Wikipedia pageviews.")
    a("- Dias macro (NFP/CPI/PPI/Retail) podem correlacionar tudo para 1 e dominar qualquer tese idiossincrática.")
    a("- **Isto é análise probabilística, não garantia nem aconselhamento personalizado.**")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
