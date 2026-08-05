# -*- coding: utf-8 -*-
"""v12-A2: autopsia da perda — o achado nº1 da investigação de 2026-08-05.

A colheita de moonshots está EV-negativa (−4,96%/evento) e o gargalo é a
PERDA MÉDIA no lado errado (−8% vs breakeven −2,6%), não o hit-rate. Este
estudo reconstrói os picks top-3 diários em walk-forward (harness dos 30
folds ancorados, o mesmo do tribunal) e disseca o bucket não-ganho.

Pergunta PRÉ-REGISTADA (v12§1): existe subgrupo excluível (n≥100) que trunque
E[y | y<0] dos picks de −8% para ≥−5%? O que sair daqui é CANDIDATO a filtro
para tribunal v13 — nunca adoção direta. Também produz a aritmética Kelly com
os números medidos (linha de sizing honesta do brief).

Uso: .venv/bin/python -m studies.loss_autopsy  → studies/loss_autopsy.md
"""
import json
import os

import numpy as np
import pandas as pd

from src import config
from src.gbm_engine import FEATS, GBM_PARAMS, MIN_TRAIN, N_FOLDS, _fit_calibrated, _gbm_mean


def sector_of(sym, cache={}):
    if sym not in cache:
        try:
            cache[sym] = json.load(open(f"data/info_{sym}.json"))["data"].get("sector") or "?"
        except Exception:
            cache[sym] = "?"
    return cache[sym]


def md(rows, header, fmt="{:.2f}"):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        cells = [fmt.format(c) if isinstance(c, float) and np.isfinite(c)
                 else ("—" if isinstance(c, float) else str(c)) for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def collect_picks():
    """Reconstrói, fold a fold (harness idêntico ao tribunal), os top-3 diários
    por p_up20 e por gbm_ev no slice de teste — com condicionantes por pick."""
    p = pd.read_csv("output/factor_panel.csv")
    p = p[p.y.notna() & (p.y.abs() <= 1.0)].sort_values("event_date").reset_index(drop=True)
    X = p[FEATS].astype(float).values
    y = p.y.values
    edges = np.linspace(MIN_TRAIN, len(p), N_FOLDS + 1).astype(int)
    picks = []
    for f in range(N_FOLDS):
        a, b = edges[f], edges[f + 1]
        if b <= a:
            continue
        med = np.nanmedian(X[:a], axis=0)
        Xtr = np.where(np.isnan(X[:a]), med, X[:a])
        Xte = np.where(np.isnan(X[a:b]), med, X[a:b])
        gm = _gbm_mean(Xtr, y[:a])
        clf20 = _fit_calibrated(Xtr, (y[:a] >= config.BIG_UP20).astype(int))
        te = p.iloc[a:b].copy()
        te["pred_ev"] = gm.predict(Xte)
        te["pred_p20"] = clf20.predict_proba(Xte)[:, 1] if clf20 is not None else np.nan
        for dte, g in te.groupby("event_date"):
            for strat, col in (("p20", "pred_p20"), ("spine", "pred_ev")):
                top = g.nlargest(3, col)
                for _, r in top.iterrows():
                    picks.append({"strat": strat, "date": dte, "ticker": r.ticker,
                                  "y": r.y, "pred_p20": r.pred_p20, "pred_ev": r.pred_ev,
                                  "log_dollar_vol": r.get("log_dollar_vol"),
                                  "log_close": r.get("log_close"), "vix": r.vix,
                                  "prior_avg_move": r.prior_avg_move})
    return pd.DataFrame(picks)


def main():
    pk = collect_picks()
    L = ["# Autopsia da perda — picks walk-forward top-3 diários (harness do tribunal)",
         f"\n*{len(pk)} picks reconstruídos ({pk[pk.strat=='p20'].shape[0]} da estratégia "
         f"moonshot/p20, {pk[pk.strat=='spine'].shape[0]} da espinha/EV) sobre "
         f"{pk.date.nunique()} dias de teste. Pergunta pré-registada v12§1.*"]
    a = L.append
    kelly_notes = {}

    for strat, nome in (("p20", "MOONSHOT (top-3 por P≥+20%)"), ("spine", "ESPINHA (top-3 por EV)")):
        d = pk[pk.strat == strat].copy()
        d["sector"] = [sector_of(t) for t in d.ticker]
        win = d.y >= config.BIG_UP20 if strat == "p20" else d.y > 0
        loss = d[d.y < 0]
        a(f"\n## Estratégia {nome}")
        a(f"- n={len(d)} picks | P(win)={win.mean():.1%} | P(y<0)={100*(d.y<0).mean():.0f}% | "
          f"E[y|win]={100*d[win].y.mean():+.1f}% | **E[y|y<0]={100*loss.y.mean():+.2f}%** | "
          f"EV bruto/pick={100*d.y.mean():+.2f}%")
        p_, W, Ln, Pn = win.mean(), d[win].y.mean(), loss.y.mean(), (d.y < 0).mean()
        ev = p_ * W + Pn * Ln + (1 - p_ - Pn) * d[(~win) & (d.y >= 0)].y.mean() if len(d[(~win) & (d.y >= 0)]) else p_ * W + Pn * Ln
        kelly_notes[strat] = dict(p=p_, W=W, L=Ln, Pneg=Pn, ev=d.y.mean())

        # decomposição do bucket de perda
        for col, nome_c in (("pred_p20", "decil de P(≥20%) prevista"),
                            ("log_dollar_vol", "quartil de liquidez"),
                            ("log_close", "quartil de preço"),
                            ("vix", "quartil de VIX"),
                            ("prior_avg_move", "quartil de volatilidade histórica")):
            dd = d.dropna(subset=[col]).copy()
            if len(dd) < 200:
                continue
            q = pd.qcut(dd[col], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
            rows = []
            for lab, g in dd.groupby(q, observed=True):
                gl = g[g.y < 0]
                rows.append([str(lab), len(g), f"{100*(g.y<0).mean():.0f}%",
                             100 * gl.y.mean() if len(gl) else np.nan,
                             100 * g.y.mean()])
            a(f"\n### Por {nome_c}")
            a(md(rows, ["Grupo", "n", "P(y<0)", "E[y|y<0] %", "EV/pick %"]))
        # setor (só grupos n>=30)
        rows = []
        for s, g in d.groupby("sector"):
            if len(g) < 30:
                continue
            gl = g[g.y < 0]
            rows.append([s, len(g), f"{100*(g.y<0).mean():.0f}%",
                         100 * gl.y.mean() if len(gl) else np.nan, 100 * g.y.mean()])
        rows.sort(key=lambda r: r[3] if isinstance(r[3], float) and np.isfinite(r[3]) else 0)
        a("\n### Por setor (n≥30)")
        a(md(rows, ["Setor", "n", "P(y<0)", "E[y|y<0] %", "EV/pick %"]))

    # veredito pré-registado: existe subgrupo excluível?
    a("\n## Veredito da pergunta pré-registada")
    d = pk[pk.strat == "p20"].dropna(subset=["prior_avg_move"]).copy()
    q4 = d[d.prior_avg_move >= d.prior_avg_move.quantile(0.75)]
    resto = d[d.prior_avg_move < d.prior_avg_move.quantile(0.75)]
    a(f"- Candidato mais óbvio (excluir quartil topo de vol histórica): perda média do resto "
      f"= {100*resto[resto.y<0].y.mean():+.2f}% (n={len(resto)}) vs {100*d[d.y<0].y.mean():+.2f}% total; "
      f"MAS o quartil topo contém {100*(q4.y>=config.BIG_UP20).sum()/max((d.y>=config.BIG_UP20).sum(),1):.0f}% "
      f"dos moonshots capturados — excluí-lo corta a razão de ser da estratégia.")
    a("- Qualquer filtro daqui vai a TRIBUNAL v13; nada é adotado neste estudo (v12§1).")

    # aritmética Kelly medida
    a("\n## Aritmética Kelly com os números MEDIDOS (para o rodapé do brief)")
    for strat, k in kelly_notes.items():
        b_, aa = k["W"], -k["L"]
        f_kelly = (k["p"] * b_ - k["Pneg"] * aa) / (aa * b_) if aa and b_ else float("nan")
        a(f"- **{strat}**: P(win)={k['p']:.1%}, E[win]={100*k['W']:+.1f}%, "
          f"P(y<0)={k['Pneg']:.0%}, E[y|y<0]={100*k['L']:+.2f}%, EV/pick={100*k['ev']:+.2f}% "
          f"→ Kelly f*={f_kelly:+.2f} ({'apostar ZERO' if f_kelly <= 0 else f'¼-Kelly={f_kelly/4:.1%} do bankroll'})")

    md_txt = "\n".join(L)
    open("studies/loss_autopsy.md", "w").write(md_txt)
    print("OK: studies/loss_autopsy.md")
    for strat, k in kelly_notes.items():
        print(f"  {strat}: P(win)={k['p']:.1%} E[win]={100*k['W']:+.1f}% "
              f"E[y|y<0]={100*k['L']:+.2f}% EV={100*k['ev']:+.2f}%")


if __name__ == "__main__":
    main()
