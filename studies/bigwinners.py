# -*- coding: utf-8 -*-
"""v10: anatomia dos "moonshots" — eventos com y >= +20% no dia do report.

Índice e limiares PRÉ-REGISTADOS na metodologia v10 (§10) ANTES de correr.
Lê output/factor_panel.csv (não reconstrói) e escreve studies/bigwinners.md
— corrige o defeito do bigmovers.py, que era print-only e nunca guardou nada.

Uso: .venv/bin/python -m studies.bigwinners
"""
import json
import os
from datetime import date

import numpy as np
import pandas as pd

UP, DN = 0.20, -0.20
STUDY_START = "2019-08-01"          # janela primária: 7 anos (fixa)
VIX_BINS = [0, 15, 25, 999]        # bins fixos pré-registados
VIX_LABELS = ["VIX<15", "VIX 15-25", "VIX>25"]
FEATURES = ["prior_avg_move", "dist_52w_high", "rsi14", "mom60", "rel_volume",
            "sandbag", "prior_up_big_rate", "vix", "n_events_same_day",
            "log_close", "log_dollar_vol"]


def md_table(df, floatfmt="{:.1f}"):
    """DataFrame -> markdown (sem dependência de tabulate)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, float) and np.isfinite(v)
                 else ("—" if isinstance(v, float) else str(v)) for v in r]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def rates_by(d, key):
    g = d.groupby(key, observed=True)
    out = g.agg(n=("y", "size"), p_up20=("big_up", "mean"), p_dn20=("big_dn", "mean"),
                media_y=("y", "mean")).reset_index()
    for c in ["p_up20", "p_dn20", "media_y"]:
        out[c] = 100 * out[c]
    return out


def quartile_profile(d, col):
    dd = d.dropna(subset=[col]).copy()
    if len(dd) < 200:
        return None
    try:
        dd["q"] = pd.qcut(dd[col], 4, labels=["Q1 (baixo)", "Q2", "Q3", "Q4 (alto)"],
                          duplicates="drop")
    except ValueError:
        return None
    return rates_by(dd, "q").rename(columns={"q": col})


def sector_of(sym, cache={}):
    if sym in cache:
        return cache[sym]
    s = None
    try:
        s = json.load(open(f"data/info_{sym}.json"))["data"].get("sector")
    except Exception:
        pass
    cache[sym] = s or "?"
    return cache[sym]


def main():
    full = pd.read_csv("output/factor_panel.csv")
    full = full[full.y.notna()].copy()
    full["big_up"] = full.y >= UP
    full["big_dn"] = full.y <= DN
    full["year"] = full.event_date.str[:4]
    d = full[full.event_date >= STUDY_START].copy()

    L = []
    a = L.append
    a(f"# Estudo big-winners v10 — eventos com y ≥ +20% no dia do report")
    a(f"\n*Gerado {date.today().isoformat()} por studies/bigwinners.py; índice e "
      f"limiares pré-registados na metodologia v10 §10 ANTES de correr. "
      f"y = reação close→close (AMC: D→D+1; BMO: D−1→D), fórmula única de reactions.py.*")

    # 1. QA
    a("\n## 1. QA do painel")
    a(f"- Painel completo: **{len(full)}** eventos, {full.ticker.nunique()} tickers, "
      f"{full.event_date.min()} → {full.event_date.max()}.")
    a(f"- Janela primária do estudo (≥{STUDY_START}, 7 anos): **{len(d)}** eventos, "
      f"{d.ticker.nunique()} tickers.")
    nan_pct = (100 * d[FEATURES].isna().mean()).round(1)
    a(f"- NaN por feature (janela do estudo): " +
      "; ".join(f"{k} {v}%" for k, v in nan_pct.items()) + ".")
    a("- **VIÉS DE SOBREVIVÊNCIA DECLARADO**: o painel nasce do universo de HOJE — "
      "deslistados/adquiridos 2019-2025 estão ausentes. Todas as taxas abaixo são "
      "CONDICIONAIS a \"sobreviveu até 2026\". Blow-ups que saíram de bolsa não contam "
      "para a cauda negativa — ela está SUBESTIMADA.")

    # 2. Taxas-base
    a("\n## 2. Taxas-base")
    a(f"- Janela do estudo: **P(y≥+20%) = {100*d.big_up.mean():.2f}%** ({d.big_up.sum()} eventos) | "
      f"**P(y≤−20%) = {100*d.big_dn.mean():.2f}%** ({d.big_dn.sum()}) | média y = {100*d.y.mean():+.2f}%.")
    a("\n### Por ano")
    a(md_table(rates_by(d, "year")))
    a("\n### Por regime VIX (bins fixos pré-registados)")
    dd = d.dropna(subset=["vix"]).copy()
    dd["regime"] = pd.cut(dd.vix, VIX_BINS, labels=VIX_LABELS)
    a(md_table(rates_by(dd, "regime")))

    # 3. Perfis por quartil
    a("\n## 3. Perfis por quartil — P(≥+20%) SEMPRE ao lado de P(≤−20%)")
    a("*As colunas p_up20/p_dn20/media_y estão em %. A pergunta honesta não é só "
      "\"onde vivem os moonshots\" mas \"o que mais vive lá\".*")
    for col in FEATURES:
        t = quartile_profile(d, col)
        if t is not None:
            a(f"\n### {col}")
            a(md_table(t))
    a("\n### log_mcap (CONTEXTO APENAS — look-ahead declarado: mcap de hoje em eventos históricos)")
    t = quartile_profile(d, "log_mcap")
    if t is not None:
        a(md_table(t))
    a("\n### Timing e dia da semana")
    a(md_table(rates_by(d, "is_amc").rename(columns={"is_amc": "AMC=1"})))
    a(md_table(rates_by(d, "dow").rename(columns={"dow": "dow (0=2ª)"})))

    # 4. Interação 2D pré-registada
    a("\n## 4. Interação log_close × prior_avg_move (única interação pré-registada)")
    dd = d.dropna(subset=["log_close", "prior_avg_move"]).copy()
    dd["q_price"] = pd.qcut(dd.log_close, 4, labels=["preço Q1", "Q2", "Q3", "Q4"])
    dd["q_vol"] = pd.qcut(dd.prior_avg_move, 4, labels=["vol Q1", "Q2", "Q3", "Q4"])
    piv_up = dd.pivot_table(index="q_vol", columns="q_price", values="big_up",
                            aggfunc="mean", observed=True) * 100
    piv_n = dd.pivot_table(index="q_vol", columns="q_price", values="big_up",
                           aggfunc="size", observed=True)
    a("\nP(y≥+20%) em %:")
    a(md_table(piv_up.reset_index()))
    a("\nn por célula:")
    a(md_table(piv_n.reset_index(), floatfmt="{:.0f}"))
    piv_dn = dd.pivot_table(index="q_vol", columns="q_price", values="big_dn",
                            aggfunc="mean", observed=True) * 100
    a("\nP(y≤−20%) em % (a mesma célula, o outro lado da moeda):")
    a(md_table(piv_dn.reset_index()))

    # 5. Repeat offenders
    a("\n## 5. Repeat offenders — os moonshots repetem-se?")
    s = d.sort_values(["ticker", "event_date"]).copy()
    s["prior8_bigup"] = (s.groupby("ticker")["big_up"]
                          .transform(lambda g: g.shift(1).rolling(8, min_periods=1).max()))
    known = s.dropna(subset=["prior8_bigup"])
    r1 = known[known.prior8_bigup == 1]
    r0 = known[known.prior8_bigup == 0]
    a(f"- P(y≥+20% | ≥1 big-up nos 8 eventos prévios) = **{100*r1.big_up.mean():.2f}%** (n={len(r1)})")
    a(f"- P(y≥+20% | 0 big-ups nos 8 prévios) = **{100*r0.big_up.mean():.2f}%** (n={len(r0)})")
    a(f"- ...e a cauda negativa nas mesmas condições: {100*r1.big_dn.mean():.2f}% vs {100*r0.big_dn.mean():.2f}%.")
    bu = d[d.big_up]
    conc = bu.ticker.value_counts()
    a(f"- Concentração: {len(conc)} tickers geram {len(bu)} moonshots; "
      f"o top-10% dos tickers gera {100*conc.head(max(1, len(conc)//10)).sum()/len(bu):.0f}% deles.")
    a(f"- Top-20 por contagem: " +
      ", ".join(f"{t} ({c})" for t, c in conc.head(20).items()) + ".")

    # 6. Mecanismo
    a("\n## 6. Mecanismo (SÓ conhecido APÓS o print — não negociável ex-ante)")
    dd = d.dropna(subset=["surprise_at_k"]).copy()
    dd["surp"] = pd.cut(dd.surprise_at_k, [-np.inf, 0, 5, 15, np.inf],
                        labels=["miss (≤0)", "beat 0-5%", "beat 5-15%", "beat >15%"])
    a(md_table(rates_by(dd, "surp").rename(columns={"surp": "surpresa EPS"})))
    bu2 = dd[dd.big_up]
    a(f"- Dos {len(bu2)} moonshots com surpresa conhecida: "
      f"{100*(bu2.surprise_at_k > 0).mean():.0f}% tiveram beat; "
      f"{100*(bu2.surprise_at_k > 15).mean():.0f}% tiveram beat >15%.")

    # 7. Perfil-lotaria pré-declarado
    a("\n## 7. Perfil-lotaria pré-declarado (quartil topo de prior_avg_move ∧ metade inferior de log_close)")
    dd = d.dropna(subset=["prior_avg_move", "log_close"]).copy()
    thr_vol = dd.prior_avg_move.quantile(0.75)
    thr_px = dd.log_close.median()
    prof = dd[(dd.prior_avg_move >= thr_vol) & (dd.log_close <= thr_px)]
    rest = dd[~((dd.prior_avg_move >= thr_vol) & (dd.log_close <= thr_px))]
    ratio = prof.big_up.mean() / prof.big_dn.mean() if prof.big_dn.mean() > 0 else np.nan
    a(f"- Perfil: n={len(prof)} ({100*len(prof)/len(dd):.0f}% dos eventos). "
      f"**P(≥+20%) = {100*prof.big_up.mean():.2f}%** vs resto {100*rest.big_up.mean():.2f}%.")
    a(f"- **P(≤−20%) = {100*prof.big_dn.mean():.2f}%** vs resto {100*rest.big_dn.mean():.2f}% — "
      f"rácio up:down no perfil = **{ratio:.2f}**.")
    a(f"- Média y no perfil: {100*prof.y.mean():+.2f}% | mediana {100*prof.y.median():+.2f}% "
      f"(a média pode viver das caudas; a mediana conta a história do evento típico).")
    a("\n### EV bruto por ano de \"comprar todos os eventos do perfil\" (SEM custos/slippage — declarado)")
    a(md_table(rates_by(prof, "year")))

    # 8. Setor
    a("\n## 8. Setor (info de hoje — look-ahead residual declarado; setor é quase-estático)")
    d2 = d.copy()
    d2["sector"] = [sector_of(t) for t in d2.ticker]
    tbl = rates_by(d2, "sector").sort_values("p_up20", ascending=False)
    tbl = tbl[tbl.n >= 100]
    a(md_table(tbl))

    a("\n---\n*Este estudo é descritivo. A passagem a features/modelo faz-se "
      "exclusivamente via tribunal v10 (gates pré-registados na metodologia). "
      "Perfis com P(≥+20%) alta têm SEMPRE P(≤−20%) alta ao lado — volatilidade "
      "não é direção. Nada aqui é recomendação.*")

    md = "\n".join(L)
    with open("studies/bigwinners.md", "w") as f:
        f.write(md)
    print(f"OK: studies/bigwinners.md ({len(md)//1024} KB)")
    print(f"Base: P(up20)={100*d.big_up.mean():.2f}% P(dn20)={100*d.big_dn.mean():.2f}% "
          f"n={len(d)} | perfil-lotaria: up {100*prof.big_up.mean():.2f}% / dn {100*prof.big_dn.mean():.2f}% "
          f"(rácio {ratio:.2f})")


if __name__ == "__main__":
    main()
