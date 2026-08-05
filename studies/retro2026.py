# -*- coding: utf-8 -*-
"""v11: auditoria retrospetiva — os maiores moonshots de 2026 e a classificação
que o sistema teria dado EX-ANTE (treinado SÓ com eventos < 2026-01-01).

Zero conhecimento do resultado: features do painel são point-in-time por
construção; o modelo é congelado no fim de 2025 (mais conservador do que o
walk-forward real, que re-treina a cada fold). Ranks calculados DENTRO do
próprio dia de calendário — a pergunta do brief ("em que lugar estaria?").

Caveats declarados: universo = painel (sobreviventes com ≥260d de preços e ≥4
eventos prévios — IPOs recentes ficam fora); flags forenses não são simuláveis
(sem fundamentais PIT) → simula-se o Radar v11 (sem filtro de veto) com o piso
de liquidez; o day_n do painel é menor que o universo real do brief.

Uso: .venv/bin/python -m studies.retro2026  → studies/retro2026.md
"""
import numpy as np
import pandas as pd

from src import config
from src.gbm_engine import FEATS, _fit_calibrated, _gbm_mean

CUT = "2026-01-01"
FLOOR = getattr(config, "RADAR_MIN_LOG_DVOL", 7.0)


def md_table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    p = pd.read_csv("output/factor_panel.csv").sort_values("event_date").reset_index(drop=True)
    p = p[p.y.notna() & (p.y.abs() <= 1.0)]
    tr, te = p[p.event_date < CUT], p[p.event_date >= CUT].copy()

    Xtr = tr[FEATS].astype(float).values
    med = np.nanmedian(Xtr, axis=0)
    Xtr = np.where(np.isnan(Xtr), med, Xtr)
    Xte = np.where(np.isnan(te[FEATS].astype(float).values), med,
                   te[FEATS].astype(float).values)
    gm = _gbm_mean(Xtr, tr.y.values)
    clf5 = _fit_calibrated(Xtr, (tr.y.values >= 0.05).astype(int))
    clf20 = _fit_calibrated(Xtr, (tr.y.values >= config.BIG_UP20).astype(int))
    te["sim_ev"] = gm.predict(Xte)
    te["sim_p5"] = clf5.predict_proba(Xte)[:, 1]
    te["sim_p20"] = clf20.predict_proba(Xte)[:, 1]

    te["day_n"] = te.groupby("event_date").ticker.transform("count")
    te["rank_spine"] = te.groupby("event_date").sim_ev.rank(ascending=False, method="min")
    te["liq_ok"] = te.log_dollar_vol >= FLOOR
    liq = te[te.liq_ok].copy()
    liq["rank_radar"] = liq.groupby("event_date").sim_p20.rank(ascending=False, method="min")
    te = te.merge(liq[["ticker", "event_date", "rank_radar"]],
                  on=["ticker", "event_date"], how="left")

    L = [f"# Retro-2026 — o que o sistema teria dito na véspera dos moonshots do ano",
         f"\n*Modelo congelado a {CUT} (treino: {len(tr)} eventos ≤2025); avaliados "
         f"{len(te)} eventos de 2026. Features point-in-time; zero conhecimento do "
         f"resultado. Radar simulado = regra v11 (sem veto-filter, piso ${10**FLOOR/1e6:.0f}M/dia). "
         f"Universo = painel (sobrevivência + ≥260d preços + ≥4 eventos — IPOs de fora).*"]
    a = L.append

    top = te.nlargest(25, "y")
    rows = []
    for _, r in top.iterrows():
        radar = (f"{int(r.rank_radar)}º" if pd.notna(r.rank_radar)
                 else ("ilíquida" if not r.liq_ok else "—"))
        hit5 = "✅" if pd.notna(r.rank_radar) and r.rank_radar <= 5 else ""
        rows.append([r.ticker, r.event_date, f"{100*r.y:+.0f}%",
                     f"{100*r.sim_p20:.1f}%", f"{radar}/{int(r.day_n)} {hit5}",
                     f"{100*r.sim_ev:+.1f}%", f"{int(r.rank_spine)}º",
                     f"{100*r.sim_p5:.0f}%"])
    a("\n## Os 25 maiores moonshots de 2026 — e a classificação ex-ante")
    a(md_table(rows, ["Ticker", "Data", "y real", "P(≥+20%) ex-ante",
                      "Rank Radar/dia", "EV ex-ante", "Rank espinha", "P(≥+5%)"]))

    moons = te[te.y >= 0.20]
    rest = te[te.y < 0.20]
    base = te.sim_p20.median()
    cap5 = moons[moons.rank_radar <= 5]
    cap1 = moons[moons.rank_radar == 1]
    liq_moons = moons[moons.liq_ok]
    a("\n## Agregados honestos")
    a(f"- Moonshots de 2026 no painel: **{len(moons)}** de {len(te)} eventos "
      f"({100*len(moons)/len(te):.1f}%); {len(liq_moons)} acima do piso de liquidez.")
    a(f"- P(≥+20%) ex-ante mediana: **{100*moons.sim_p20.median():.1f}%** nos moonshots "
      f"vs {100*rest.sim_p20.median():.1f}% no resto (mediana global {100*base:.1f}%) — "
      f"rácio {moons.sim_p20.median()/rest.sim_p20.median():.1f}×.")
    a(f"- **Radar top-5 do próprio dia apanhou {len(cap5)} dos {len(liq_moons)} moonshots "
      f"líquidos ({100*len(cap5)/max(len(liq_moons),1):.0f}%)**; nº 1 do Radar: {len(cap1)}.")
    picks5 = liq[liq.rank_radar <= 5]
    prec = (picks5.y >= 0.20).mean()
    a(f"- Precisão do Radar top-5 em 2026: {100*prec:.1f}% dos picks deram ≥+20% "
      f"(base do ano: {100*(te.y >= 0.20).mean():.1f}%) — lift {prec/(te.y>=0.20).mean():.1f}×.")
    a(f"- Espinha (gbm_ev): {len(moons[moons.rank_spine <= 3])} dos {len(moons)} moonshots "
      f"estavam no top-3 do dia por EV; {len(moons[moons.rank_spine == 1])} eram o nº 1.")
    a("\n*Leitura: o sistema não 'sabe' quem vai explodir — sabe QUEM É CANDIDATO. "
      "A distância entre a mediana ex-ante dos moonshots e a base é o edge real; "
      "o resto é a lotaria que as probabilidades calibradas sempre declararam. "
      "Flags forenses não simuláveis; day_n do painel < universo real do brief.*")

    md = "\n".join(L)
    open("studies/retro2026.md", "w").write(md)
    print(f"OK: studies/retro2026.md | moonshots 2026: {len(moons)} | "
          f"radar-top5 capturou {len(cap5)}/{len(liq_moons)} líquidos | "
          f"mediana p20 ex-ante {100*moons.sim_p20.median():.1f}% vs resto {100*rest.sim_p20.median():.1f}%")


if __name__ == "__main__":
    main()
