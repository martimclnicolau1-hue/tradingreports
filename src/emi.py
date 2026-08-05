# -*- coding: utf-8 -*-
"""v12-B1: EMI — Expectations Management Index (Johnson-Kim-So, RFS 2020).

Prevê QUEM está incentivado e equipado para gerir expectativas e "fabricar"
um beat: cobertura de analistas (COV) + posse institucional (INST) + sales
growth (SG) + distância à falência (ALT). Efeito documentado: 64-88bps/mês
no mês do anúncio (n=320k firm-quarters). Média simples de percentis — os
autores confirmam robustez vs PCA (loadings COV 0,48 / INST 0,49 dominam).

VERSÃO 1 (declarada, metodologia v12§5): inputs 100% do disco, zero fetches:
- COV: numberOfAnalystOpinions do info cache (fallback: snapshot do dia)
- INST: heldPercentInstitutions do info cache
- SG: revenueGrowth do info cache (PROXY do 5-year weighted do paper —
  upgrade para XBRL 5 anos quando o painel de snapshots maturar)
- ALT: altman_z2 já no candidatos.csv
CONTEXTO com zero peso; validação prospetiva (sem histórico PIT grátis).

Uso: .venv/bin/python -m src.emi   (após rescore; escreve coluna emi no CSV)
"""
import glob
import json
import os

import numpy as np
import pandas as pd


def _info(sym):
    try:
        return json.load(open(f"data/info_{sym}.json"))["data"]
    except Exception:
        return {}


def main():
    df = pd.read_csv("output/candidatos.csv")
    cov, inst, sg = [], [], []
    for s in df.ticker:
        i = _info(s)
        cov.append(i.get("numberOfAnalystOpinions"))
        inst.append(i.get("heldPercentInstitutions"))
        sg.append(i.get("revenueGrowth"))
    df["_cov"], df["_inst"], df["_sg"] = cov, inst, sg

    # fallback de COV: snapshot de estimativas do dia (ee_0q_numberOfAnalysts)
    snaps = sorted(glob.glob("data/estimates/*.csv.gz"))
    if snaps and df["_cov"].isna().mean() > 0.3:
        try:
            sn = pd.read_csv(snaps[-1])
            col = next((c for c in sn.columns if "numberOfAnalysts" in c and c.startswith("ee_0")), None)
            if col:
                m = sn.set_index("ticker")[col]
                df["_cov"] = df["_cov"].fillna(df.ticker.map(m))
        except Exception:
            pass

    # percentis cross-section entre os anunciantes da janela + média simples
    comps = []
    for c in ["_cov", "_inst", "_sg", "altman_z2"]:
        s = pd.to_numeric(df[c], errors="coerce")
        comps.append(s.rank(pct=True))
    emi = pd.concat(comps, axis=1).mean(axis=1, skipna=True)
    n_comp = pd.concat(comps, axis=1).notna().sum(axis=1)
    df["emi"] = np.where(n_comp >= 3, emi.round(3), np.nan)  # exige ≥3 dos 4 inputs
    df.drop(columns=["_cov", "_inst", "_sg"]).to_csv("output/candidatos.csv", index=False)
    ok = df.emi.notna()
    print(f"EMI: {ok.sum()}/{len(df)} candidatos com ≥3 inputs | "
          f"top-5: {df[ok].nlargest(5, 'emi')[['ticker','emi']].values.tolist()}")


if __name__ == "__main__":
    main()
