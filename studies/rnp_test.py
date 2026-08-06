# -*- coding: utf-8 -*-
"""v12-B3: P-calibrada vs P-implícita (risk-neutral) — o único teste de
monetização de cauda que vale (metodologia v12§6; não-executante).

P_RN(S>K̄) ≈ [C(K1)−C(K2)]/(K2−K1) com K1≈1,15×spot, K2≈1,25×spot (call
spread digital na primeira expiração pós-evento), mids do arquivo de chains.
NaN quando o spread bid-ask >30% do mid (iliquidez) ou strikes em falta.

EXPECTATIVA PRÉ-REGISTADA: perder (prémios de variância e jump inflacionam
P_RN acima da P física) — mas o log acumulado decide com dados, não opinião.
Append diário a data/rnp_log.csv; veredito mensal no monitor.

Uso: .venv/bin/python -m studies.rnp_test   (após chain_archive, no noturno)
"""
import os
from datetime import date

import numpy as np
import pandas as pd

LOG = "data/rnp_log.csv"


def p_rn_from_chain(snap, spot):
    """P_RN(≥+20%) por call-spread nos strikes disponíveis mais próximos."""
    c = snap[snap.side == "C"].dropna(subset=["bid", "ask"]).copy()
    c = c[(c.bid > 0) & (c.ask > 0)]
    if len(c) < 4:
        return np.nan
    c["mid"] = (c.bid + c.ask) / 2
    c = c[(c.ask - c.bid) / c.mid <= 0.30]      # filtro de liquidez (registado na metodologia v13§4)
    if len(c) < 2:
        return np.nan
    k1_t, k2_t = 1.15 * spot, 1.25 * spot
    k1 = c.iloc[(c.strike - k1_t).abs().argsort()].iloc[0]
    k2 = c.iloc[(c.strike - k2_t).abs().argsort()].iloc[0]
    if k2.strike <= k1.strike or abs(k1.strike - k1_t) > 0.08 * spot:
        return np.nan
    p = float((k1.mid - k2.mid) / (k2.strike - k1.strike))
    return p if 0 <= p <= 1 else np.nan


def main():
    hoje = date.today().isoformat()
    chain_path = f"data/chains/{hoje}.csv"
    if not os.path.exists(chain_path):
        # usa o snapshot mais recente disponível
        import glob
        snaps = sorted(glob.glob("data/chains/????-??-??.csv"))
        if not snaps:
            print("sem arquivo de chains — nada a fazer")
            return
        chain_path = snaps[-1]
    chains = pd.read_csv(chain_path)
    cand = pd.read_csv("output/candidatos.csv")
    cand = cand[cand.p_up20_cal.notna() & cand.event_date.notna()]
    rows = []
    for _, r in cand.iterrows():
        snap = chains[chains.ticker == r.ticker]
        if snap.empty:
            continue
        spot = float(snap.spot.iloc[0])
        p_rn = p_rn_from_chain(snap, spot)
        if np.isnan(p_rn):
            continue
        rows.append({"asof": chain_path[-14:-4], "ticker": r.ticker,
                     "event_date": r.event_date, "spot": round(spot, 2),
                     "p_cal": round(float(r.p_up20_cal), 4), "p_rn": round(p_rn, 4),
                     "edge_cal_vs_rn": round(float(r.p_up20_cal) - p_rn, 4)})
    if not rows:
        print("RN-P: 0 pares hoje (chains ilíquidas ou sem candidatos p20)")
        return
    df = pd.DataFrame(rows)
    hdr = not os.path.exists(LOG)
    df.to_csv(LOG, mode="a", header=hdr, index=False)
    pos = (df.edge_cal_vs_rn > 0).mean()
    print(f"RN-P: {len(df)} pares registados | P_cal>P_RN em {100*pos:.0f}% | "
          f"mediana P_cal {df.p_cal.median():.3f} vs P_RN {df.p_rn.median():.3f}")
    print(df.nlargest(5, "edge_cal_vs_rn").to_string(index=False))


if __name__ == "__main__":
    main()
