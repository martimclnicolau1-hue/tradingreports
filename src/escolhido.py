# -*- coding: utf-8 -*-
"""v13.1: O ESCOLHIDO DO DIA — email de UM nome com o caso fundamental por extenso.

Seleção INALTERADA (v8§5: topo do gbm_ev entre elegíveis sem flags forenses,
no âmbito do brief). Mudança de apresentação apenas: em vez de tabelas, o
email explica em prosa o caso A FAVOR (fundamentais, expectativas, posição
short, sinais de opções) e o caso CONTRA, com percentis vs os candidatos do
dia. O brief completo continua a ser gerado e arquivado localmente.

Uso: [EVENTCAL_TODAY=1] .venv/bin/python -m src.escolhido
  → output/escolhido_YYYY-MM-DD.{md,html}
"""
import json
import os
from datetime import date, datetime, timedelta

import pandas as pd

from . import config

TODAY_MODE = os.environ.get("EVENTCAL_TODAY") == "1"


def _info(sym):
    try:
        return json.load(open(f"data/info_{sym}.json"))["data"]
    except Exception:
        return {}


def _pct(x, nd=1):
    return "—" if x is None or pd.isna(x) else f"{100*float(x):.{nd}f}%"


def _pctile(df, col, v):
    """Percentil do valor v na distribuição não-nula do dia (0-100)."""
    if col not in df.columns or pd.isna(v):
        return None
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 20:
        return None
    return round(100 * float((s < float(v)).mean()))


def build_escolhido(csv_path="output/candidatos.csv"):
    T = date.today()
    t1, t2 = T + timedelta(days=1), T + timedelta(days=2)
    d_amc, d_bmo, dl = (T, t1, T) if TODAY_MODE else (t1, t2, t1)
    df = pd.read_csv(csv_path).dropna(subset=["event_date"])
    df["veto_flags"] = df["veto_v3"].fillna("") if "veto_v3" in df.columns else ""
    opp = df[((df.event_date == d_amc.isoformat()) & (df.timing.isin(["AMC", "?"]))) |
             ((df.event_date == d_bmo.isoformat()) & (df.timing == "BMO"))].copy()
    el = opp[(opp.veto_flags == "") & opp.gbm_ev.notna() & opp.p_up5_cal.notna()].copy()
    if el.empty:
        md = ("# Sem escolhido hoje\n\nNenhum candidato elegível (sem flags, com score) "
              "na janela — dias vazios são informação, não falha.")
        _write(md, T)
        return None
    # v13.2 ADOTADO: EV ajustado ao risco — "mais provável de subir mais COM segurança"
    # (tribunal 2026-08-06: P(neg) do top-1 56,7%→46,7% com média igual)
    el["rank_escolhido"] = el.gbm_ev / (el.gbm_q90 - el.gbm_q10).clip(lower=1e-6)
    pick = el.sort_values("rank_escolhido", ascending=False).iloc[0]
    i = _info(pick.ticker)
    nome = i.get("shortName") or pick.ticker
    setor = i.get("sector") or "—"

    L = []
    a = L.append
    a(f"# 🎯 O Escolhido — {pick.ticker} ({nome})")
    a(f"\n*{setor} · reporta {pd.Timestamp(pick.event_date).strftime('%d/%m')} "
      f"{pick.timing} · prazo de decisão: **{dl.strftime('%d/%m')} às 21:00 de Lisboa** · "
      f"gerado {T.isoformat()} {datetime.now().strftime('%H:%M')}.*")

    # ---- os números do modelo, traduzidos
    a("\n## Porque é o nº 1 de hoje")
    a(f"É o topo do motor entre {len(el)} candidatos limpos do dia: retorno esperado "
      f"**{_pct(pick.gbm_ev)}**, com **{_pct(pick.p_up5_cal, 0)}** de probabilidade calibrada "
      f"de subir ≥5% e **{_pct(pick.get('p_up20_cal'), 1)}** de subir ≥20%. Em 8 de cada 10 "
      f"casos históricos análogos, o desfecho ficou entre **{_pct(pick.gbm_q10)}** e "
      f"**{_pct(pick.gbm_q90)}** — este intervalo é a régua honesta do risco.")

    # ---- fundamentais em prosa, com percentil do dia
    a("\n## Os fundamentais, explicados")
    fund = []
    rg = i.get("revenueGrowth")
    if rg is not None:
        p = _pctile(df, "score", None)  # placeholder não usado
        fund.append(f"- **Receita a crescer {_pct(rg, 0)}/ano** — "
                    + ("crescimento forte; earnings de nomes em aceleração reagem mais aos beats."
                       if rg > 0.15 else
                       "crescimento moderado/baixo — o print vive mais da margem e do guidance do que da receita."))
    gm = i.get("grossMargins")
    if gm is not None:
        fund.append(f"- **Margem bruta {_pct(gm, 0)}** — "
                    + ("margem alta: cada dólar extra de receita cai quase direto no lucro (alavanca operacional)."
                       if gm > 0.5 else "margem industrial/baixa: os beats dependem de volume e custos, não de preço."))
    az = pick.get("altman_z2")
    if pd.notna(az):
        fund.append(f"- **Altman Z'' {az:.1f}** — " + ("balanço sólido, risco de insolvência remoto."
                    if az > 2.6 else ("zona cinzenta de solidez — vigiar dívida." if az > 1.1
                    else "zona de stress — é por isto que teria flag (não tem: verificar).")))
    sbc = pick.get("sbc_pct_revenue")
    if pd.notna(sbc):
        fund.append(f"- **Stock-based comp {_pct(sbc, 0)} da receita** — "
                    + ("baixa: os lucros são 'de verdade', pouca diluição." if sbc < 0.08 else
                       "relevante: parte do lucro contabilístico paga-se em diluição dos acionistas."))
    acc = pick.get("sloan_accruals")
    if pd.notna(acc):
        fund.append(f"- **Accruals {_pct(acc, 0)}** — "
                    + ("negativos/baixos: lucros suportados por caixa real (qualidade alta)."
                       if acc < 0.03 else "elevados: lucros à frente da caixa — qualidade a vigiar."))
    if fund:
        L += fund
    else:
        a("*Fundamentais snapshot indisponíveis para este nome (dados yfinance em falta).*")

    # ---- o jogo das expectativas
    a("\n## O jogo das expectativas (o que decide o dia do report)")
    br = pick.get("beat_rate_8q"); sb = pick.get("sandbag_surprise_4q"); bf = pick.get("beat_and_fell_rate")
    exp = []
    if pd.notna(br):
        exp.append(f"- Bateu o consenso em **{_pct(br, 0)}** dos últimos 8 trimestres" +
                   (" — máquina de beats." if br >= 0.75 else "."))
    if pd.notna(sb):
        if sb > 20:
            leitura = "sandbagging clássico: guiam baixo, esmagam depois."
        elif sb < -15:
            leitura = "⚠ falha o consenso POR HÁBITO — os analistas estão sistematicamente otimistas com este nome."
        else:
            leitura = "surpresas contidas — o consenso anda perto da realidade."
        exp.append(f"- Surpresa média recente **{sb:+.0f}%** vs consenso — {leitura}")
    if pd.notna(bf):
        exp.append(f"- MAS bateu-e-caiu em **{_pct(bf, 0)}** dos beats — "
                   + ("quase nunca: quando bate, o mercado paga." if bf < 0.2 else
                      "às vezes bater não chega; as expectativas embutidas são o verdadeiro listão."))
    emi = pick.get("emi")
    if pd.notna(emi):
        exp.append(f"- EMI {emi:.2f} (percentil {_pctile(df, 'emi', emi)} do dia) — "
                   "mede cobertura de analistas + posse institucional + incentivos a 'fabricar' um beat "
                   "(Johnson-Kim-So: alto EMI = +64-88bps no mês do anúncio, historicamente).")
    L += exp

    # ---- o lado do mercado (short + opções)
    lado = []
    dtc = pick.get("days_to_cover"); dsi = pick.get("dsi_pct"); spf = pick.get("short_pct_float")
    if pd.notna(dtc):
        lado.append(f"- **Days-to-cover {dtc:.1f}** " +
                    ("— shorts levariam dias a sair: combustível de squeeze se o print for bom."
                     if dtc > 5 else "— posição short ligeira."))
    if pd.notna(dsi):
        lado.append(f"- Short interest {'a subir' if dsi > 0.02 else ('a descer' if dsi < -0.02 else 'estável')} "
                    f"({_pct(dsi, 1)} vs quinzena anterior).")
    cp = pick.get("cpiv"); sm = pick.get("smirk")
    if pd.notna(cp):
        lado.append(f"- Opções: CPIV {100*cp:+.1f}pp ({'calls mais caras — inclinação bullish' if cp > 0 else 'puts mais caras — proteção procurada'}; "
                    "contexto do nosso arquivo, zero peso).")
    if pd.notna(sm) and abs(sm) < 0.5:  # |smirk|≥50pp = cadeia ilíquida, não sinal
        lado.append(f"- Smirk {100*sm:+.1f}pp ({'proteção OTM cara — cautela institucional' if sm > 0.05 else 'smirk plano — sem pânico embutido'}).")
    im = pick.get("implied_move_pct"); am = pick.get("avg_abs_move")
    if pd.notna(im) and pd.notna(am):
        lado.append(f"- O mercado preça um movimento de **{_pct(im)}**; o histórico dela move "
                    f"**{_pct(am)}** — edge {pick.get('edge_ratio'):.2f}" +
                    (" (o bilhete está barato vs o hábito)." if pd.notna(pick.get('edge_ratio')) and pick.get('edge_ratio') > 1.1 else
                     " (o bilhete está caro ou justo vs o hábito)." if pd.notna(pick.get('edge_ratio')) else "."))
    if lado:
        a("\n## O que o mercado está a dizer")
        L += lado

    # ---- o caso contra
    a("\n## O caso CONTRA (lê isto antes de decidires)")
    a(f"- Probabilidade de **cair**: ~{_pct(1 - pick.p_up, 0) if pd.notna(pick.get('p_up')) else '≈45%'} — "
      f"e quando cai, a queda média dos análogos é {_pct(pick.get('downside'))}.")
    a(f"- O intervalo de 80% inclui {_pct(pick.gbm_q10)} — perder isto num dia é cenário normal, não extremo.")
    a(f"- Movimento típico dela em earnings: {_pct(am) if pd.notna(am) else '—'} para QUALQUER lado; "
      f"stops não protegem através de gaps.")
    if pd.notna(pick.get("pct_missing")) and pick.pct_missing > 0.4:
        a(f"- ⚠ {_pct(pick.pct_missing, 0)} dos campos de dados em falta — leitura menos fiável.")
    if not pick.get("date_verified"):
        a("- ⚠ Data do evento não confirmada por 2ª fonte — confirmar no IR.")

    a("\n---")
    a("*O sistema nomeia o nº 1 pela regra pré-registada e explica porquê — a decisão e o "
      "tamanho são teus. P calibrada = frequência histórica verificada, não convicção. "
      f"Brief completo (Radar, Estreantes, tabelas) em output/brief_{T.isoformat()}.md.*")

    md = "\n".join(L)
    return _write(md, T)


def _write(md, T):
    md_path = f"output/escolhido_{T.isoformat()}.md"
    open(md_path, "w").write(md)
    import re
    html_lines = []
    for raw in md.split("\n"):
        line = raw.strip()
        if not line or line == "---":
            continue
        if line.startswith("# "):
            html_lines.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("## "):
            html_lines.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            html_lines.append(f"<p>{line}</p>")
    html = "<div style='font-family:sans-serif;max-width:680px;line-height:1.5'>" + "\n".join(html_lines) + "</div>"
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
    html = re.sub(r"\*(.+?)\*", r"<i>\1</i>", html)
    html_path = f"output/escolhido_{T.isoformat()}.html"
    open(html_path, "w").write(html)
    print(f"OK: {md_path} + {html_path}")
    return md_path, html_path


if __name__ == "__main__":
    build_escolhido()
