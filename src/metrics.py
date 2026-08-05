# -*- coding: utf-8 -*-
"""Camada de cálculo: reações históricas a earnings, edge ratio, técnica,
scores forenses e o score composto PRÉ-REGISTADO (ver output/metodologia.md).

REGRA: os pesos e fórmulas daqui foram fixados ANTES de qualquer dado ser
descarregado. Não os alteres depois de veres resultados — isso é p-hacking.
"""
import math

import numpy as np
import pandas as pd

from . import config


# ---------------------------------------------------------------------------
# Reações históricas a earnings (AMC/BMO tratado corretamente)
# ---------------------------------------------------------------------------
def earnings_reactions(prices, earnings_df, n=None):
    """Para cada earnings passado, o retorno close→close do dia de reação.

    AMC (após fecho): reação = dia seguinte. BMO (antes da abertura):
    reação = próprio dia. O yfinance dá timestamps com hora — usa-se a hora
    para inferir o timing; >=16h ET conta como AMC.
    """
    n = n or config.N_PAST_EARNINGS
    if prices is None or earnings_df is None or earnings_df.empty:
        return []
    idx = prices.index.tz_localize(None).normalize()
    closes = prices["Close"].values
    out = []
    now = pd.Timestamp.utcnow().tz_localize(None)
    past = earnings_df[earnings_df["date"].dt.tz_localize(None) < now]
    for _, row in past.head(n).iterrows():
        ts = row["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0  # meia-noite = data sem hora → assume AMC (mais comum)
        day = pd.Timestamp(ts.date())
        pos = idx.searchsorted(day)
        if amc:
            before, after = pos, pos + 1
        else:
            before, after = pos - 1, pos
        if before < 0 or after >= len(closes):
            continue
        ret = closes[after] / closes[before] - 1
        # drift D+2/D+3 a partir do fecho do dia de reação
        drift = None
        if after + 3 < len(closes):
            drift = closes[after + 3] / closes[after] - 1
        out.append({"date": str(day.date()), "amc": bool(amc), "reaction": float(ret),
                    "drift_d3": None if drift is None else float(drift)})
    return out


def reaction_stats(reactions):
    if not reactions:
        return {}
    r = np.array([x["reaction"] for x in reactions])
    big = config.BIG_MOVE_THRESHOLD
    n = len(r)
    up_big = float((r >= big).mean())
    dn_big = float((r <= -big).mean())
    # IC binomial (Wilson) para a taxa de movimentos grandes positivos —
    # honestidade de amostra pequena exigida pelo STEP 4
    p = up_big
    z = 1.96
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    drifts_after_up = [x["drift_d3"] for x in reactions if x["reaction"] > 0 and x["drift_d3"] is not None]
    return {
        "n": n,
        "avg_abs_move": float(np.abs(r).mean()),
        "median_abs_move": float(np.median(np.abs(r))),
        "skew_pct": up_big - dn_big,          # % quarters >=+10% menos % <=-10%
        "pct_up_big": up_big,
        "pct_dn_big": dn_big,
        "up_big_ci95": (max(0.0, centre - half), min(1.0, centre + half)),
        "worst": float(r.min()),
        "best": float(r.max()),
        "drift_d3_after_up_avg": float(np.mean(drifts_after_up)) if drifts_after_up else None,
    }


# ---------------------------------------------------------------------------
# Bloco de expectativas/surpresas (v2) — o fundamental mais relevante a 1–2d
# ---------------------------------------------------------------------------
def surprise_stats(earnings_df, reactions):
    """Beat rate, momentum de surpresa e taxa 'beat-and-fell' a partir dos
    dados reais de Surprise(%) do yfinance + reações de preço calculadas."""
    if earnings_df is None or earnings_df.empty:
        return {}
    col = next((c for c in earnings_df.columns if "surprise" in c.lower()), None)
    if col is None:
        return {}
    past = earnings_df.dropna(subset=[col]).copy()
    if past.empty:
        return {}
    surp = past[col].astype(float).head(8)  # mais recente primeiro
    n = len(surp)
    beat_rate = float((surp > 0).mean())
    momentum = None
    if n >= 8:
        momentum = float(surp.iloc[:4].mean() - surp.iloc[4:8].mean())
    # beat-and-fell: bateu o EPS mas a reação de preço foi negativa
    rx = {r["date"]: r["reaction"] for r in reactions}
    beats = fells = 0
    for _, row in past.head(8).iterrows():
        d = str(pd.Timestamp(row["date"]).date()) if "date" in past.columns else None
        if d is None or d not in rx:
            continue
        if float(row[col]) > 0:
            beats += 1
            if rx[d] < 0:
                fells += 1
    # v8: shrinkage empírico-Bayes para a média global do painel (peso n/(n+8))
    _PRIORS = {"beat": 0.68, "n0": 8}
    try:
        import os as _os
        if _os.path.exists("output/factor_panel.csv"):
            import pandas as _pd
            _pb = _pd.read_csv("output/factor_panel.csv", usecols=["prior_beat_rate"])
            _PRIORS["beat"] = float(_pb.prior_beat_rate.mean())
    except Exception:
        pass
    w = n / (n + _PRIORS["n0"])
    beat_rate = w * beat_rate + (1 - w) * _PRIORS["beat"]
    return {
        "beat_rate_8q": beat_rate,
        "surprise_momentum": momentum,          # >0 = surpresas a melhorar
        "beat_and_fell_rate": (fells / beats) if beats else None,  # alto = fasquia alta
        "n_surprises": n,
    }


# ---------------------------------------------------------------------------
# Forense (aprox. com dados yfinance; campos em falta → None, nunca inventar)
# ---------------------------------------------------------------------------
def _get(df, names, col=0):
    if df is None or df.empty:
        return None
    for nm in names:
        if nm in df.index:
            try:
                v = df.loc[nm].iloc[col]
                return None if pd.isna(v) else float(v)
            except Exception:
                continue
    return None


def forensic_scores(fin):
    """Altman Z, accruals (Sloan), conversão FCF/NI, SBC%%. Aproximações
    declaradas: sem dados completos devolve None em vez de estimar."""
    inc, bal, cf = fin.get("income"), fin.get("balance"), fin.get("cashflow")
    out = {}
    ta = _get(bal, ["Total Assets"])
    tl = _get(bal, ["Total Liabilities Net Minority Interest", "Total Liab"])
    ca = _get(bal, ["Current Assets", "Total Current Assets"])
    cl = _get(bal, ["Current Liabilities", "Total Current Liabilities"])
    re_ = _get(bal, ["Retained Earnings"])
    ebit = _get(inc, ["EBIT", "Operating Income"])
    rev = _get(inc, ["Total Revenue"])
    ni = _get(inc, ["Net Income"])
    ocf = _get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"])
    capex = _get(cf, ["Capital Expenditure"])
    sbc = _get(cf, ["Stock Based Compensation"])

    if all(v is not None for v in [ta, tl, ca, cl, re_, ebit, rev]) and ta:
        wc = ca - cl
        # Altman Z'' (não-industrial, sem market cap): 6.56X1+3.26X2+6.72X3+1.05X4
        out["altman_z2"] = 6.56 * wc / ta + 3.26 * re_ / ta + 6.72 * ebit / ta + 1.05 * (ta - tl) / ta
    if ni is not None and ocf is not None and ta:
        out["sloan_accruals"] = (ni - ocf) / ta      # >0.10 = sinal de alerta
    if ni and ocf is not None and capex is not None:
        fcf = ocf + capex  # capex vem negativo no yfinance
        out["fcf_ni_conversion"] = fcf / ni if ni != 0 else None
    if sbc is not None and rev:
        out["sbc_pct_revenue"] = sbc / rev
    return out


# ---------------------------------------------------------------------------
# SCORE COMPOSTO PRÉ-REGISTADO v2 — 65% fundamental / 35% quant
# (revisão registada em metodologia.md ANTES da 1ª execução; não mexer depois)
# ---------------------------------------------------------------------------
def _clip01(x):
    return max(0.0, min(1.0, x))


def composite_score(info, forensics, rstats, implied, surprises=None, rev_accel=None):
    """v2. Campos em falta valem 0.5 (neutro) e contam para `missing` —
    um score cheio de neutros é fraco por definição; o relatório mostra a
    % de dados em falta ao lado do score, sempre."""
    surprises = surprises or {}
    missing = []

    def val(x, lo, hi, invert=False, name=""):
        if x is None:
            missing.append(name)
            return 0.5
        v = _clip01((x - lo) / (hi - lo))
        return 1 - v if invert else v

    # --- Bloco 1: expectativas/surpresas (30% do fundamental) ---
    e_beat = val(surprises.get("beat_rate_8q"), 0.3, 0.9, name="beat_rate")
    e_mom = val(surprises.get("surprise_momentum"), -10.0, 10.0, name="surprise_momentum")
    e_fell = val(surprises.get("beat_and_fell_rate"), 0.0, 0.6, invert=True, name="beat_and_fell")
    expectations = 0.40 * e_beat + 0.25 * e_mom + 0.35 * e_fell

    # --- Bloco 2: crescimento + aceleração + margem (25%) ---
    g_growth = val(info.get("revenueGrowth"), 0.0, 0.5, name="revenueGrowth")
    g_accel = val(rev_accel, -0.10, 0.10, name="rev_acceleration")
    g_margin = val(info.get("grossMargins"), 0.2, 0.8, name="grossMargins")
    growth = 0.45 * g_growth + 0.30 * g_accel + 0.25 * g_margin

    # --- Bloco 3: qualidade dos lucros (25%) ---
    q_fcf = val(forensics.get("fcf_ni_conversion"), 0.0, 1.5, name="fcf_conversion")
    q_accrual = val(forensics.get("sloan_accruals"), -0.1, 0.15, invert=True, name="sloan")
    q_sbc = val(forensics.get("sbc_pct_revenue"), 0.02, 0.25, invert=True, name="sbc")
    quality = 0.40 * q_fcf + 0.35 * q_accrual + 0.25 * q_sbc

    # --- Bloco 4: sobrevivência + valuation (20%) ---
    s_altman = val(forensics.get("altman_z2"), 0.0, 6.0, name="altman_z2")
    netcash = None
    if info.get("marketCap"):
        tc, td = info.get("totalCash"), info.get("totalDebt")
        if tc is not None and td is not None:
            netcash = (tc - td) / info["marketCap"]
    s_netcash = val(netcash, -0.3, 0.3, name="net_cash_mcap")
    ev_s, g = info.get("enterpriseToRevenue"), info.get("revenueGrowth")
    if ev_s and g and g > 0:
        s_valgrowth = _clip01(1 - (ev_s / (g * 100)) / 0.6)
    else:
        s_valgrowth = 0.5
        missing.append("ev_s_vs_growth")
    surviv = 0.40 * s_altman + 0.30 * s_netcash + 0.30 * s_valgrowth

    fundamental = 0.30 * expectations + 0.25 * growth + 0.25 * quality + 0.20 * surviv

    # --- Quant (35%): edge 50 / skew 35 / drift 15 (PEAD morto p/ large caps) ---
    q_skew = val(rstats.get("skew_pct"), -0.4, 0.6, name="skew")
    edge = None
    if implied and rstats.get("avg_abs_move"):
        im = implied.get("implied_move_pct")
        if im:
            edge = rstats["avg_abs_move"] / im
    q_edge = val(edge, 0.6, 1.5, name="edge_ratio")
    q_drift = val(rstats.get("drift_d3_after_up_avg"), -0.03, 0.06, name="drift")
    quant = 0.50 * q_edge + 0.35 * q_skew + 0.15 * q_drift

    total = 100 * (0.65 * fundamental + 0.35 * quant)
    return total, {
        "fundamental_0_1": round(fundamental, 3),
        "quant_0_1": round(quant, 3),
        "expectations_0_1": round(expectations, 3),
        "edge_ratio": None if edge is None else round(edge, 2),
        "missing_fields": missing,
        "pct_missing": round(len(missing) / 16, 2),
    }
