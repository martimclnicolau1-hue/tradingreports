# -*- coding: utf-8 -*-
"""v6: brief diário de oportunidades (enviado às 21:45 de Lisboa).

Âmbito do brief gerado no dia T:
- Eventos AMC de T+1 (prazo de entrada: T+1 às 21:00 de Lisboa)
- Eventos BMO de T+2 (prazo: T+1 às 21:00)
- Eventos BMO de T+1 aparecem só como "amanhã de manhã" (prazo já passou)

Graus (regra fixa, metodologia v6): A = sem vetos + data verificada + dois
estimadores concordam <1,5× + edge conservador ≥1,0 + beat&fell <50%;
B = sem vetos + data verificada, estimador único ou edge 0,8–1,0; C = vigia.

O brief é INFORMATIVO: graus e prazos, sem diretivas de compra/venda.
Uso: .venv/bin/python -m src.daily_brief  → output/brief_YYYY-MM-DD.{md,html}
"""
from datetime import date, timedelta

import pandas as pd

from . import config

# v10: aviso bicaudal do Radar — números medidos no estudo de 2026-08-05
# (studies/bigwinners.md, 22.086 eventos); constante datada, refrescada só em re-estudo.
RADAR_TAIL = ("no perfil que produz P(≥+20%)=10,0%, a queda ≥20% acontece 5,9% das "
              "vezes — mais de metade do tamanho (estudo 2026-08-05, n=22.086). "
              "Volatilidade não é direção.")


def _grade(r):
    a, b = r.get("edge_ratio"), r.get("edge_ratio_clean")
    have_a, have_b = pd.notna(a), pd.notna(b)
    agree = have_a and have_b and min(a, b) > 0 and max(a, b) / min(a, b) < 1.5
    emin = min([x for x in (a, b) if pd.notna(x)], default=None)
    bf = r.get("beat_and_fell_rate")
    if (agree and emin is not None and emin >= 1.0
            and (pd.isna(bf) or bf < 0.5) and r.get("date_verified")):
        return "A"
    if r.get("date_verified") and emin is not None and emin >= 0.8:
        return "B"
    return "C"


def _fmt(x, pct=False, nd=1):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{100*x:.{nd}f}%" if pct else f"{x}"


def _row_md(r):
    return (f"| {r['ticker']} | {r.get('timing','?')} | {_fmt(r.get('score_v4') or r.get('score'))} "
            f"| {_fmt(r.get('edge_ratio'))}/{_fmt(r.get('edge_ratio_clean'))} "
            f"| {_fmt(round(r.get('sandbag_surprise_4q'),0) if pd.notna(r.get('sandbag_surprise_4q')) else None)} | {_fmt(r.get('dist_52w_high'), pct=True, nd=0)} "
            f"| {_fmt(r.get('beat_and_fell_rate'), pct=True, nd=0)} "
            f"| {_fmt(r.get('avg_abs_move'), pct=True)} |")


HEADER_MD = "| Ticker | Timing | Score | Edge (str/clean) | Sandbag | vs Máx52s | Beat&Fell | Mov. hist. |\n|---|---|---|---|---|---|---|---|"


def build_brief(today=None, csv_path="output/candidatos.csv"):
    T = today or date.today()
    t1, t2 = T + timedelta(days=1), T + timedelta(days=2)
    df = pd.read_csv(csv_path).dropna(subset=["event_date"])
    df["_vetoed"] = df.get("veto_v3", pd.Series(dtype=str)).notna() & (df.get("veto_v3", "") != "")

    opp = df[((df.event_date == t1.isoformat()) & (df.timing == "AMC")) |
             ((df.event_date == t2.isoformat()) & (df.timing == "BMO"))].copy()
    morning_info = df[(df.event_date == t1.isoformat()) & (df.timing == "BMO")]

    el = opp[~opp._vetoed].copy()
    el["grade"] = el.apply(_grade, axis=1)
    el = el.sort_values(["grade", "score_v4" if "score_v4" in el else "score"],
                        ascending=[True, False])

    L = []
    a = L.append
    a(f"# Brief earnings — oportunidades com prazo {t1.strftime('%d/%m')} às 21:00 de Lisboa")
    a(f"\n*Gerado {T.isoformat()} ~21:45. Cobre: eventos após o fecho de {t1.strftime('%d/%m')} "
      f"e antes da abertura de {t2.strftime('%d/%m')}. Prazo único de decisão: "
      f"**{t1.strftime('%d/%m')} às 21:00 de Lisboa**.*")

    # posições do utilizador com evento próximo
    pos_events = df[df.ticker.isin(config.EXISTING_POSITIONS) &
                    df.event_date.isin([t1.isoformat(), t2.isoformat()])]
    if not pos_events.empty:
        a("\n## ⚠ As tuas posições com evento nesta janela")
        for _, r in pos_events.iterrows():
            a(f"- **{r.ticker}** ({config.EXISTING_POSITIONS[r.ticker]}): reporta "
              f"{pd.Timestamp(r.event_date).strftime('%d/%m')} {r.timing}")

    if not morning_info.empty:
        names = ", ".join(morning_info.sort_values("score", ascending=False).ticker.head(8))
        a(f"\n*Amanhã de manhã (prazo já encerrado): {names}*")

    # v8: PICK DE MAIOR CONFIANÇA + abstenção (manchete)
    import json as _json, os as _os
    val = {}
    if _os.path.exists("output/gbm_validation.json"):
        val = _json.load(open("output/gbm_validation.json"))
    if "p_up5_cal" in el.columns and el.p_up5_cal.notna().any() and val:
        cand = el[el.p_up5_cal.notna()].sort_values("gbm_ev", ascending=False)
        pick = cand.iloc[0] if len(cand) else None
        limiar = val.get("abstencao", {}).get("limiar", 0.65)
        if pick is not None and pick.p_up5_cal >= limiar:
            # frase de auditoria do bucket correspondente
            audit = ""
            for c in val.get("calibration", []):
                lo_hi = c["bucket"].strip("(]").split(",")
                try:
                    if float(lo_hi[0]) < pick.p_up5_cal <= float(lo_hi[1]):
                        small = " — amostra pequena, pouco fiável" if c["n"] < 30 else ""
                        audit = (f" (auditoria walk-forward: quando o sistema previu ~{100*c['previsto']:.0f}%, "
                                 f"aconteceu {100*c['realizado']:.0f}% das vezes, n={c['n']}{small})")
                        break
                except ValueError:
                    continue
            a(f"\n## 🎯 PICK DE MAIOR CONFIANÇA: {pick.ticker} ({pick.get('timing','?')})")
            a(f"P(subir ≥+5%) calibrada: **{100*pick.p_up5_cal:.0f}%**{audit}. "
              f"EV do modelo: {100*pick.gbm_ev:+.1f}% | intervalo conformal 80%: "
              f"[{100*pick.gbm_q10:+.1f}%; {100*pick.gbm_q90:+.1f}%]. "
              f"*Confiança calibrada ≠ garantia — significa que a percentagem anunciada "
              f"corresponde à frequência histórica verificada.*")
        else:
            a("\n## SEM SINAL DE ALTA CONFIANÇA HOJE")
            best = f"{pick.ticker} com {100*pick.p_up5_cal:.0f}%" if pick is not None else "—"
            a(f"*Nenhum candidato atingiu P(≥+5%) calibrada ≥ {100*limiar:.0f}% (melhor: {best}). "
              f"O sistema abstém-se por regra — dias sem sinal são informação, não falha.*")

    # v10: RADAR +20% — só publica se a cabeça p20 passou os gates do tribunal
    gates = {}
    if _os.path.exists("output/gates_v10.json"):
        gates = _json.load(open("output/gates_v10.json"))
    if gates.get("adota_cabeca_p20") and "p_up20_cal" in el.columns and el.p_up20_cal.notna().any():
        radar = el[el.p_up20_cal.notna()].sort_values("p_up20_cal", ascending=False).head(3)
        a("\n## 🚀 RADAR +20% — candidatos a movimento grande")
        a("| Ticker | Timing | P(≥+20%) calibrada | EV | Intervalo conformal 80% |")
        a("|---|---|---|---|---|")
        for _, r in radar.iterrows():
            a(f"| {r.ticker} | {r.get('timing','?')} | **{100*r.p_up20_cal:.0f}%** "
              f"| {100*r.gbm_ev:+.1f}% | [{100*r.gbm_q10:+.1f}%; {100*r.gbm_q90:+.1f}%] |")
        a(f"*Moonshots são raros: estas probabilidades são honestas e tipicamente 5-20% — "
          f"correspondem à frequência verificada em walk-forward, não a convicção. "
          f"AVISO BICAUDAL: {RADAR_TAIL}*")

    # v7: RANKING POR VALOR ESPERADO (topo do brief)
    if "ev_knn" in el.columns and el.ev_knn.notna().any():
        import json as _json, os as _os
        verdict, n_scored = "—", None
        if _os.path.exists("output/ev_validation.json"):
            _evv = _json.load(open("output/ev_validation.json"))
            verdict, n_scored = _evv.get("verdict", "—"), _evv.get("n_scored")
        a("\n## RANKING POR VALOR ESPERADO (EV) — top 10 não vetados")
        a(f"*Validação walk-forward (n={n_scored if n_scored else '—'} eventos): {verdict}.*")
        a("| Ticker | Timing | EV | P(subir) | P(≥+10%) | E[subida] | Cauda top-10% | E[queda] | IC95 EV | Hype | Grau | Cresc. | Marg. | Short% | CPIV | O/S |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        evtop = el[el.ev_knn.notna()].sort_values("ev_knn", ascending=False).head(10)
        for _, r in evtop.iterrows():
            hy = r.get("hype_score")
            hy_s = "—" if pd.isna(hy) else ("ALTO" if hy >= 70 else ("médio" if hy >= 40 else "baixo"))
            ci = f"[{100*r.ev_ci_lo:+.1f};{100*r.ev_ci_hi:+.1f}]" if pd.notna(r.get("ev_ci_lo")) else "—"
            a(f"| {r.ticker} | {r.get('timing','?')} | **{100*r.ev_knn:+.1f}%** "
              f"| {100*r.p_up:.0f}% | {100*r.p_big:.0f}% | {100*r.e_up:+.1f}% "
              f"| {100*r.tail_up:+.1f}% | {100*r.downside:+.1f}% | {ci} | {hy_s} | {r.get('grade','')} "
              f"| {_fmt(r.get('rev_acceleration'), pct=True, nd=0) if pd.notna(r.get('rev_acceleration')) else '—'} "
              f"| {_fmt(r.get('sbc_pct_revenue'), pct=True, nd=0) if pd.notna(r.get('sbc_pct_revenue')) else '—'} "
              f"| {_fmt(r.get('short_pct_float'), pct=True, nd=0) if pd.notna(r.get('short_pct_float')) else '—'} "
              f"| {f'{100*r.cpiv:+.1f}pp' if pd.notna(r.get('cpiv')) else '—'} "
              f"| {f'{r.os_ratio:.1f}' if pd.notna(r.get('os_ratio')) else '—'} |")
        a("*EV estimado por 50 analogs históricos — ordenação com erro largo, não previsão. "
          "Hype = atenção social atual; a literatura documenta subida de curto prazo seguida de REVERSÃO após picos. "
          "CPIV = spread IV call−put ATM do nosso arquivo (positivo = calls caras, inclinação bullish documentada); "
          "O/S = volume de opções ÷ volume de ações. Ambos CONTEXTO com zero peso; caveat "
          "Muravyev-Pearson-Pollet: ~2/3 destes sinais refletem borrow fees, não informação.*")
    elif "ev_knn" not in el.columns:
        a("\n*EV não calculado neste ciclo.*")

    for g, title in [("A", "GRAU A — passam todos os filtros de qualidade"),
                     ("B", "GRAU B — sólidos com uma reserva (estimador único ou edge 0,8–1,0)"),
                     ("C", "GRAU C — vigia (não vetados, sem edge citável)")]:
        sub = el[el.grade == g]
        if sub.empty:
            if g == "A":
                a(f"\n## {title}\n*Nenhum candidato atingiu o grau A neste ciclo — dias sem grau A são normais e são informação.*")
            continue
        a(f"\n## {title}")
        a(HEADER_MD)
        for _, r in sub.head(10 if g != "C" else 5).iterrows():
            a(_row_md(r))

    vet = opp[opp._vetoed]
    if not vet.empty:
        a("\n## Vetados (forense manda)")
        for _, r in vet.sort_values("score", ascending=False).head(8).iterrows():
            a(f"- {r.ticker}: {r.veto_v3}")

    macro = [m for m in config.MACRO_EVENTS if m["date"] in (t1, t2)]
    if macro:
        a("\n## Macro na janela")
        for m in macro:
            a(f"- **{m['date'].strftime('%d/%m')}** — {m['name']} às "
              f"{int(m['time_et'][:2])+5}:{m['time_et'][3:]} de Lisboa ({m['source']})")

    a("\n---")
    a("*Este brief é informação, não recomendação de compra ou venda. Cada secção cita "
      "o seu próprio veredito de validação sem lookahead — o que não estiver marcado "
      "como validado é indistinguível de ruído; os graus medem a qualidade do setup, "
      "não a probabilidade de lucro. As quotes de opções são do fecho — reconfirma no "
      "próprio dia. Stops não protegem através de gaps; o tamanho da posição é o único "
      "controlo real. O EV vem de analogs históricos com IC largo (veredito citado na "
      "própria secção). Decisões são tuas.*")

    md = "\n".join(L)
    md_path = f"output/brief_{T.isoformat()}.md"
    with open(md_path, "w") as f:
        f.write(md)

    # HTML simples para corpo de email
    import re
    html_lines = []
    flat = [l for item in L for l in item.split("\n")]
    for raw in flat:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            html_lines.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("## "):
            html_lines.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= {"-", " "}:
                continue
            tag = "th" if set(cells[0]) <= {"-"} or cells[0] == "Ticker" else "td"
            html_lines.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.strip() in ("---", ""):
            continue
        else:
            html_lines.append(f"<p>{line}</p>")
    html = ("<div style='font-family:sans-serif;max-width:720px'>"
            + "\n".join(html_lines).replace("<tr><th", "<table border='1' cellpadding='4' style='border-collapse:collapse'><tr><th")
            + "</div>")
    html = re.sub(r"(</tr>)(?!\n?<tr>)", r"\1</table>", html)
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
    html = re.sub(r"\*(.+?)\*", r"<i>\1</i>", html)
    html_path = f"output/brief_{T.isoformat()}.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"OK: {md_path} + {html_path} | grau A: {len(el[el.grade=='A'])} · B: {len(el[el.grade=='B'])} · C: {len(el[el.grade=='C'])}")
    return md_path, html_path


if __name__ == "__main__":
    build_brief()
