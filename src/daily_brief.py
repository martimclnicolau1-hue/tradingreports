# -*- coding: utf-8 -*-
"""v6→v11: brief diário de oportunidades (enviado às 21:45 de Lisboa).

Âmbito do brief gerado no dia T (modo standard, pós-fecho às 21:45):
- Eventos AMC de T+1 (prazo de entrada: T+1 às 21:00 de Lisboa)
- Eventos BMO de T+2 (prazo: T+1 às 21:00)

Modo PRÉ-FECHO (EVENTCAL_TODAY=1, gerado ANTES das 21:00 de Lisboa):
- Eventos AMC de HOJE + BMO de amanhã — prazo de entrada HOJE às 21:00.

Regime v11 (metodologia v11, pré-registada 2026-08-05):
- Espinha única: gbm_ev (cabeça) + p_up20_cal (Radar). Graus A/B/C abolidos.
- CABEÇA exige zero flags forenses (regra v8§5 intacta).
- RADAR mostra 🚩flags sem excluir + piso de liquidez RADAR_MIN_LOG_DVOL
  (excluídos pelo piso são listados, nunca silenciosos).
- Tabela EV do anexo mantém a regra v7 (vetado fora — o EV é média).
- Secção "Fábricas de moonshots" — próximos reports dos maiores produtores
  históricos de y≥+20% (responde a "porque não está a PLTR": janela de 7d).

O brief é INFORMATIVO: probabilidades calibradas e prazos, sem diretivas.
Uso: .venv/bin/python -m src.daily_brief  → output/brief_YYYY-MM-DD.{md,html}
"""
import json
import os
from datetime import date, datetime, timedelta

import pandas as pd

from . import config

TODAY_MODE = os.environ.get("EVENTCAL_TODAY") == "1"

# v10: aviso bicaudal do Radar — números medidos no estudo de 2026-08-05
# (studies/bigwinners.md, 22.086 eventos); constante datada, refrescada só em re-estudo.
RADAR_TAIL = ("no perfil que produz P(≥+20%)=10,0%, a queda ≥20% acontece 5,9% das "
              "vezes — mais de metade do tamanho (estudo 2026-08-05, n=22.086). "
              "Volatilidade não é direção.")


def _fmt(x, pct=False, nd=1):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{100*x:.{nd}f}%" if pct else f"{x}"


def _dvol_str(ldv):
    """log10($ vol/dia) → string legível ($3M, $120M…)."""
    if ldv is None or pd.isna(ldv):
        return "—"
    v = 10 ** float(ldv)
    return f"${v/1e9:.1f}B" if v >= 1e9 else (f"${v/1e6:.0f}M" if v >= 1e6 else f"${v/1e3:.0f}k")


def _factories(top_n=8):
    """v11: maiores produtores de y≥+20% (painel, desde 2019-08) × próximo report
    na cache yfinance. Sobrevivência declarada; idade da cache mostrada se >7d."""
    try:
        pan = pd.read_csv("output/factor_panel.csv", usecols=["ticker", "event_date", "y"])
    except Exception:
        return []
    vc = pan[(pan.event_date >= "2019-08-01") & (pan.y >= 0.20)].ticker.value_counts()
    hoje = pd.Timestamp.today().normalize()
    out = []
    for t, c in vc.head(30).items():
        p = f"data/earnings_{t}.json"
        if not os.path.exists(p):
            continue
        try:
            j = json.load(open(p))
            fut = sorted(pd.Timestamp(r["date"]).tz_localize(None).normalize()
                         for r in j["data"]
                         if pd.Timestamp(r["date"]).tz_localize(None) >= hoje)
            if not fut:
                continue
            idade = (pd.Timestamp.utcnow().tz_localize(None)
                     - pd.Timestamp(j["fetched_at"]).tz_localize(None)).days
            out.append((t, int(c), fut[0].date(), idade))
        except Exception:
            continue
        if len(out) >= top_n:
            break
    return sorted(out, key=lambda x: x[2])


def build_brief(today=None, csv_path="output/candidatos.csv"):
    T = today or date.today()
    t1, t2 = T + timedelta(days=1), T + timedelta(days=2)
    # pré-fecho: AMC de hoje + BMO de amanhã, prazo hoje; standard: T+1/T+2, prazo amanhã
    d_amc, d_bmo, dl = (T, t1, T) if TODAY_MODE else (t1, t2, t1)
    df = pd.read_csv(csv_path).dropna(subset=["event_date"])
    df["veto_flags"] = df["veto_v3"].fillna("") if "veto_v3" in df.columns else ""

    # v11: timing "?" entra no braço AMC (prazo mais cedo = nunca atrasado), com flag
    opp = df[((df.event_date == d_amc.isoformat()) & (df.timing.isin(["AMC", "?"]))) |
             ((df.event_date == d_bmo.isoformat()) & (df.timing == "BMO"))].copy()
    morning_info = df.iloc[0:0] if TODAY_MODE else \
        df[(df.event_date == t1.isoformat()) & (df.timing == "BMO")]

    el = opp[opp["veto_flags"] == ""].copy()   # cabeça + tabela EV: zero flags (regra intacta)
    has_p20 = "p_up20_cal" in opp.columns
    has_ldv = "log_dollar_vol" in opp.columns
    floor = getattr(config, "RADAR_MIN_LOG_DVOL", 7.0)
    if has_p20:
        pool_all = opp[opp.p_up20_cal.notna()]
        radar_pool = pool_all[pool_all.log_dollar_vol >= floor] if has_ldv else pool_all
        # v13: "nunca silencioso" a sério — top-10 nomeados + contagem do resto
        radar_below = (pool_all[pool_all.log_dollar_vol < floor] if has_ldv
                       else pool_all.iloc[0:0])
        radar_out = radar_below.nlargest(10, "p_up20_cal")
    else:
        radar_pool = radar_out = opp.iloc[0:0]

    L = []
    a = L.append
    a(f"# Brief earnings — oportunidades com prazo {dl.strftime('%d/%m')} às 21:00 de Lisboa")
    hoje_tag = " (MODO PRÉ-FECHO: o prazo é HOJE — mercado ainda aberto)" if TODAY_MODE else ""
    a(f"\n*Gerado {T.isoformat()} às {datetime.now().strftime('%H:%M')} de Lisboa{hoje_tag}. "
      f"Cobre: eventos após o fecho de {d_amc.strftime('%d/%m')} "
      f"e antes da abertura de {d_bmo.strftime('%d/%m')}. Prazo único de decisão: "
      f"**{dl.strftime('%d/%m')} às 21:00 de Lisboa**.*")

    # v12: regime + tripwires (contexto de sizing, zero peso — metodologia v12§3-4)
    if os.path.exists("output/monitor.json"):
        mon = json.load(open("output/monitor.json"))
        rg = mon.get("regime")
        if rg:
            a(f"\n*Regime de earnings: **{rg['label']}** — {100*rg['frac_acima_habito']:.0f}% dos "
              f"últimos {rg['n']} eventos moveram acima do hábito próprio (até {rg['ate']}). "
              f"Contexto de sizing, zero peso no ranking.*")
        if mon.get("any_tripped"):
            tw = ", ".join(t["tripwire"] for t in mon["tripped"])
            a(f"\n## ⚠ TRIPWIRE DISPARADO: {tw}")
            a("*Um critério pré-registado de avaria do sistema falhou (metodologia v12§4) — "
              "tratar os rankings deste brief com desconfiança até revisão.*")

    # posições do utilizador com evento próximo
    pos_events = df[df.ticker.isin(config.EXISTING_POSITIONS) &
                    df.event_date.isin([d_amc.isoformat(), d_bmo.isoformat()])]
    if not pos_events.empty:
        a("\n## ⚠ As tuas posições com evento nesta janela")
        for _, r in pos_events.iterrows():
            a(f"- **{r.ticker}** ({config.EXISTING_POSITIONS[r.ticker]}): reporta "
              f"{pd.Timestamp(r.event_date).strftime('%d/%m')} {r.timing}")

    if not morning_info.empty:
        srt = "gbm_ev" if "gbm_ev" in morning_info.columns else "score"
        names = ", ".join(morning_info.sort_values(srt, ascending=False).ticker.head(8))
        a(f"\n*Amanhã de manhã (prazo já encerrado): {names}*")

    # CABEÇA: UM candidato + 2 alternativas (regra de seleção v8§5 intacta:
    # topo do gbm_ev entre elegíveis com zero flags)
    val = {}
    if os.path.exists("output/gbm_validation.json"):
        val = json.load(open("output/gbm_validation.json"))
    gates = {}
    if os.path.exists("output/gates_v10.json"):
        gates = json.load(open("output/gates_v10.json"))
    if "p_up5_cal" in el.columns and el.p_up5_cal.notna().any() and val:
        # v13.2 ADOTADO: cabeça ordenada por EV ajustado ao risco (= regra do Escolhido)
        cand = el[el.p_up5_cal.notna()].copy()
        cand["_ra"] = cand.gbm_ev / (cand.gbm_q90 - cand.gbm_q10).clip(lower=1e-6)
        cand = cand.sort_values("_ra", ascending=False)
        pick = cand.iloc[0] if len(cand) else None
        limiar = val.get("abstencao", {}).get("limiar", 0.65)
        if pick is not None:
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
            selo = bool(pick.p_up5_cal >= limiar)
            titulo = ("PICK DE MAIOR CONFIANÇA" if selo
                      else "CANDIDATO Nº 1 DO DIA (sem selo de alta confiança)")
            a(f"\n## 🎯 {titulo}: {pick.ticker} ({pick.get('timing','?')})")
            a(f"P(subir ≥+5%) calibrada: **{100*pick.p_up5_cal:.0f}%**{audit}. "
              f"EV do modelo: {100*pick.gbm_ev:+.1f}% | intervalo conformal 80%: "
              f"[{100*pick.gbm_q10:+.1f}%; {100*pick.gbm_q90:+.1f}%].")
            avisos = []
            if not pick.get("date_verified"):
                avisos.append("⚠ data do evento não confirmada por 2ª fonte")
            if pick.get("timing") == "?":
                avisos.append("⚠ timing (AMC/BMO) não confirmado")
            pm = pick.get("pct_missing")
            if pd.notna(pm) and pm > 0.40:  # v13: ressurreição da regra v1§1
                avisos.append(f"⚠ dados incompletos ({100*pm:.0f}% dos campos em falta)")
            if avisos:
                a("*" + " · ".join(avisos) + "*")
            if not selo:
                a(f"*Nº 1 pela regra pré-registada (maior EV entre candidatos sem flags) — não é "
                  f"garantia: o selo exige P(≥+5%) calibrada ≥{100*limiar:.0f}%, que nunca ocorreu "
                  f"em 25,6k eventos históricos. {100*pick.p_up5_cal:.0f}% também significa "
                  f"~{100*(1-pick.p_up5_cal):.0f}% de NÃO subir 5%.*")
            for i, (_, alt) in enumerate(cand.iloc[1:3].iterrows(), start=2):
                a(f"- Alternativa nº {i}: **{alt.ticker}** ({alt.get('timing','?')}) — EV {100*alt.gbm_ev:+.1f}%, "
                  f"P(≥+5%) {100*alt.p_up5_cal:.0f}%, intervalo [{100*alt.gbm_q10:+.1f}%; {100*alt.gbm_q90:+.1f}%]")
            if gates.get("adota_cabeca_p20") and len(radar_pool):
                rt = radar_pool.sort_values("p_up20_cal", ascending=False).iloc[0]
                fl = f" 🚩{rt['veto_flags']}" if rt["veto_flags"] else ""
                a(f"- 🎟 Bilhete de lotaria do dia: **{rt.ticker}**{fl} — {100*rt.p_up20_cal:.0f}% de "
                  f"P(≥+20%) calibrada, {_dvol_str(rt.get('log_dollar_vol'))}/dia (detalhe no Radar)")
            a("*O edge validado vive no CONJUNTO dos 3 primeiros (tribunal: TOP-3 +3,97%±1,60 por fold; "
              "o nº 1 sozinho rende mais em média mas com o dobro do ruído: +4,97%±3,74). "
              "Um nome único = mais variância, não mais certeza.*")

    # v11: RADAR +20% reformado — flags visíveis SEM excluir + piso de liquidez
    if gates.get("adota_cabeca_p20") and len(radar_pool):
        radar = radar_pool.sort_values("p_up20_cal", ascending=False).head(5)
        a("\n## 🚀 RADAR +20% — candidatos a movimento grande")
        a("| Ticker | Timing | P(≥+20%) | EV | Intervalo 80% | $/dia | 🚩 Flags |")
        a("|---|---|---|---|---|---|---|")
        for _, r in radar.iterrows():
            exp_flag = " ⏳" if r.get("monthly_expiry_flag") is True else ""
            a(f"| {r.ticker}{exp_flag} | {r.get('timing','?')} | **{100*r.p_up20_cal:.0f}%** "
              f"| {100*r.gbm_ev:+.1f}% | [{100*r.gbm_q10:+.1f}%; {100*r.gbm_q90:+.1f}%] "
              f"| {_dvol_str(r.get('log_dollar_vol'))} | {r['veto_flags'] or '—'} |")
        if len(radar_out):
            fora = ", ".join(f"{r.ticker} ({100*r.p_up20_cal:.0f}%, {_dvol_str(r.get('log_dollar_vol'))}/dia)"
                             for _, r in radar_out.iterrows())
            resto = len(radar_below) - len(radar_out)
            a(f"*Fora do Radar por liquidez (<{_dvol_str(floor)}/dia): {fora}"
              + (f" — e mais {resto} abaixo destes" if resto > 0 else "") + ".*")
        a(f"*v11: as flags forenses (🚩Altman/SBC/accruals/beat&fell) deixaram de excluir do Radar "
          f"— são risco visível, não proibição; a cabeça continua a exigir zero flags. Decisão "
          f"documentada na metodologia (não testável sem fundamentais point-in-time). Probabilidades "
          f"honestas, tipicamente 5-20%. AVISO BICAUDAL: {RADAR_TAIL}*")

    # v11: fábricas de moonshots — onde andam os PLTR desta vida
    fabs = _factories()
    if fabs:
        linha = " · ".join(f"**{t}** ({c}×) {d.strftime('%d/%m')}" +
                           (f" [cache {i}d]" if i > 7 else "")
                           for t, c, d, i in fabs)
        a("\n## 🏭 Fábricas de moonshots — próximos reports")
        a(linha)
        a("*Maiores produtores históricos de subidas ≥+20% no dia do report (painel 7 anos, "
          "condicional a sobrevivência) e a PRÓXIMA data de report na cache (confirmar no IR). "
          "Entram no brief quando a janela de 7 dias os apanhar — ex.: PLTR reporta em novembro; "
          "não aparecer hoje é calendário, não filtro.*")

    # v13: ESTREANTES — visibilidade sem previsão (IPOs/histórico curto; antes invisíveis)
    rookies = opp[opp.gbm_ev.isna()] if "gbm_ev" in opp.columns else opp.iloc[0:0]
    if len(rookies):
        def _mcap(t):
            try:
                mc = json.load(open(f"data/info_{t}.json"))["data"].get("marketCap")
                return float(mc) if mc else float("nan")
            except Exception:
                return float("nan")
        rk = rookies.copy()
        rk["_mcap"] = [_mcap(t) for t in rk.ticker]
        rk = rk.sort_values("_mcap", ascending=False)
        a("\n## 🌱 Estreantes — na janela mas sem score (história insuficiente para o modelo)")
        a("| Ticker | Timing | Mcap | Implied move | 🚩 Flags |")
        a("|---|---|---|---|---|")
        for _, r in rk.head(10).iterrows():
            mc = r["_mcap"]
            mc_s = "—" if pd.isna(mc) else (f"${mc/1e9:.1f}B" if mc >= 1e9 else f"${mc/1e6:.0f}M")
            im = f"{100*r.implied_move_pct:.1f}%" if pd.notna(r.get("implied_move_pct")) else "—"
            a(f"| {r.ticker} | {r.get('timing','?')} | {mc_s} | {im} | {r['veto_flags'] or '—'} |")
        if len(rk) > 10:
            a(f"*…e mais {len(rk)-10} estreantes na janela.*")
        a("*Sem score = <4 reports prévios ou <1 ano de preços — o modelo não prevê sem história "
          "(v13§2); visibilidade sem previsão fabricada. Modelo para estreantes: candidato v14.*")

    a("\n---\n\n## ANEXO — detalhe completo (podes parar de ler aqui)")

    # v7: RANKING POR VALOR ESPERADO (mantém regra v7: vetado fora — o EV é média)
    if "ev_knn" in el.columns and el.ev_knn.notna().any():
        verdict, n_scored = "—", None
        if os.path.exists("output/ev_validation.json"):
            _evv = json.load(open("output/ev_validation.json"))
            verdict, n_scored = _evv.get("verdict", "—"), _evv.get("n_scored")
        a("\n## RANKING POR VALOR ESPERADO (EV) — top 10 sem flags")
        a(f"*Validação walk-forward (n={n_scored if n_scored else '—'} eventos): {verdict}.*")
        a("| Ticker | Timing | EV | P(subir) | P(≥+10%) | E[subida] | Cauda top-10% | E[queda] | IC95 EV | Hype | Cresc. | Marg. | Short% | CPIV | O/S |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        evtop = el[el.ev_knn.notna()].sort_values("ev_knn", ascending=False).head(10)
        for _, r in evtop.iterrows():
            hy = r.get("hype_score")
            hy_s = "—" if pd.isna(hy) else ("ALTO" if hy >= 70 else ("médio" if hy >= 40 else "baixo"))
            ci = f"[{100*r.ev_ci_lo:+.1f};{100*r.ev_ci_hi:+.1f}]" if pd.notna(r.get("ev_ci_lo")) else "—"
            a(f"| {r.ticker} | {r.get('timing','?')} | **{100*r.ev_knn:+.1f}%** "
              f"| {100*r.p_up:.0f}% | {100*r.p_big:.0f}% | {100*r.e_up:+.1f}% "
              f"| {100*r.tail_up:+.1f}% | {100*r.downside:+.1f}% | {ci} | {hy_s} "
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

    flagged = opp[opp["veto_flags"] != ""]
    if not flagged.empty:
        a("\n## 🚩 Flags forenses do dia (contexto — já não excluem do Radar; a cabeça exige zero flags)")
        srt = "gbm_ev" if "gbm_ev" in flagged.columns else "score"
        for _, r in flagged.sort_values(srt, ascending=False).head(10).iterrows():
            a(f"- {r.ticker}: {r['veto_flags']}")

    macro = [m for m in config.MACRO_EVENTS if m["date"] in (d_amc, d_bmo)]
    if macro:
        a("\n## Macro na janela")
        for m in macro:
            a(f"- **{m['date'].strftime('%d/%m')}** — {m['name']} às "
              f"{int(m['time_et'][:2])+5}:{m['time_et'][3:]} de Lisboa ({m['source']})")

    a("\n---")
    a("*SIZING MEDIDO (autopsia walk-forward 2026-08-06, studies/loss_autopsy.md): os top-3 "
      "diários renderam ~+0,8%/pick com P(y<0)≈49% e perda média de −8% quando corre mal; "
      "como aposta binária na cauda, o Kelly do moonshot é ZERO — o EV vem do meio "
      "(0 a +20%), não do bilhete de lotaria. Tradução: posições pequenas, muitos eventos, "
      "nunca concentrar num nome.*")
    a("*Este brief é informação, não recomendação de compra ou venda. Cada secção cita "
      "o seu próprio veredito de validação sem lookahead — o que não estiver marcado "
      "como validado é indistinguível de ruído. Flags forenses são risco visível, não "
      "proibição (v11); a cabeça exige zero flags. As quotes de opções são do fecho — "
      "reconfirma no próprio dia. Stops não protegem através de gaps; o tamanho da "
      "posição é o único controlo real. O EV vem de analogs históricos com IC largo "
      "(veredito citado na própria secção). Decisões são tuas.*")

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
    print(f"OK: {md_path} + {html_path} | âmbito: {len(opp)} · sem flags: {len(el)} · "
          f"radar: {len(radar_pool)} (+{len(radar_out)} sob o piso) · flags: {len(opp)-len(el)}")
    return md_path, html_path


if __name__ == "__main__":
    build_brief()
