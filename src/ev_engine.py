# -*- coding: utf-8 -*-
"""v7: motor de VALOR ESPERADO por analogs históricos (kNN) + métricas de cauda.

Regras fixadas na metodologia v7 (ler antes de alterar): EV é ORDENAÇÃO, não
previsão; vetos sobrepõem-se; features em falta nunca imputadas; validação
walk-forward pré-registada com gate de publicação.

Uso: .venv/bin/python -m src.ev_engine [--selftest] [--skip-validation]
"""
import json
import sys

import numpy as np
import pandas as pd

from . import config
from .factor_study import build_panel, features_from_history, load_earnings, load_prices, _log_mcap

FEATURES = ["dist_52w_high", "rsi14", "mom60", "prior_avg_move",
            "prior_up_big_rate", "sandbag", "log_mcap", "rel_volume"]
K = 50
N_BOOT = 200
SEED = 42
MIN_FEATS_CAND = 6
MIN_SHARED_DIMS = 4
MIN_NEIGHBORS = 30
MIN_PRIOR_EVENTS_WF = 300
Z_CLIP = 3.0


def load_panel(rebuild=False):
    try:
        p = pd.read_csv("output/factor_panel.csv")
        if rebuild or not set(["event_date", "sandbag", "log_mcap", "rel_volume"]) <= set(p.columns):
            raise FileNotFoundError
    except FileNotFoundError:
        p = build_panel()
        p.to_csv("output/factor_panel.csv", index=False)
    import os as _os
    y_max = float(_os.environ.get("EVENTCAL_YMAX", "2.0"))  # v13 ADOTADO — coerente com build_panel
    p = p[p.y.notna() & (p.y.abs() <= y_max)].reset_index(drop=True)
    return p


def zparams(panel):
    X = panel[FEATURES].astype(float)
    return X.mean().values, X.std().values


def zmatrix(df, mu, sigma):
    X = df[FEATURES].astype(float).values
    Z = (X - mu) / np.where(sigma > 0, sigma, 1.0)
    return np.clip(Z, -Z_CLIP, Z_CLIP)


def masked_dist(z_cand, Z_panel):
    """Distância euclidiana mascarada; <MIN_SHARED_DIMS dims partilhadas -> inf."""
    diff2 = (Z_panel - z_cand) ** 2
    shared = (~np.isnan(diff2)).sum(axis=1)
    with np.errstate(invalid="ignore"):
        d = np.sqrt(np.nanmean(diff2, axis=1))
    d[shared < MIN_SHARED_DIMS] = np.inf
    d[np.isnan(d)] = np.inf
    return d


def ev_metrics(y):
    big = config.BIG_MOVE_THRESHOLD
    up = y[y > 0]
    dn = y[y < 0]
    ysort = np.sort(y)[::-1]
    top_dec = ysort[:max(1, len(y) // 10)]
    return {
        "ev_knn": float(y.mean()),
        "p_up": float((y > 0).mean()),
        "p_big": float((y >= big).mean()),
        "e_up": float(up.mean()) if len(up) else 0.0,
        "tail_up": float(top_dec.mean()),
        "downside": float(dn.mean()) if len(dn) else 0.0,
        "p5": float(np.percentile(y, 5)),
    }


def bootstrap_ci(y, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(y), size=(n_boot, len(y)))
    means = y[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def candidate_features(sym):
    """Featuriza o candidato pelo MESMO código do painel (paridade v7)."""
    edf, prices = load_earnings(sym), load_prices(sym)
    if edf is None or prices is None or len(prices) < 260:
        return None
    scol = next((c for c in edf.columns if "surprise" in c.lower()), None)
    idx = prices.index.tz_localize(None).normalize()
    closes = prices["Close"].values
    volumes = prices["Volume"].values if "Volume" in prices else None
    now = pd.Timestamp.utcnow().tz_localize(None)
    past = edf[edf["date"].dt.tz_localize(None) < now]
    reactions, surprises = [], []
    for _, r in past.iterrows():
        ts = r["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0
        day = pd.Timestamp(ts.date()); pos = idx.searchsorted(day)
        b, a = (pos, pos+1) if amc else (pos-1, pos)
        if b < 0 or a >= len(closes):
            continue
        reactions.append(closes[a]/closes[b]-1)
        surprises.append(float(r[scol]) if scol and pd.notna(r[scol]) else None)
    if len(reactions) < 4:
        return None
    return features_from_history(closes, volumes, reactions, surprises, _log_mcap(sym))


def tail_ratio(sym, cand_row):
    edf, prices = load_earnings(sym), load_prices(sym)
    if edf is None or prices is None:
        return None
    feats = None
    idx = prices.index.tz_localize(None).normalize()
    closes = prices["Close"].values
    now = pd.Timestamp.utcnow().tz_localize(None)
    ups = []
    for _, r in edf[edf["date"].dt.tz_localize(None) < now].iterrows():
        ts = r["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0
        day = pd.Timestamp(ts.date()); pos = idx.searchsorted(day)
        b, a = (pos, pos+1) if amc else (pos-1, pos)
        if 0 <= b and a < len(closes):
            rr = closes[a]/closes[b]-1
            if rr > 0:
                ups.append(rr)
    if len(ups) < 6:
        return None
    implied = cand_row.get("clean_event_move")
    if implied is None or (isinstance(implied, float) and pd.isna(implied)):
        implied = cand_row.get("implied_move_pct")
    if implied is None or (isinstance(implied, float) and pd.isna(implied)) or implied <= 0:
        return None
    return float(np.percentile(ups, 95) / implied)


def score_candidates(csv_path="output/candidatos.csv"):
    panel = load_panel()
    mu, sigma = zparams(panel)
    Z_panel = zmatrix(panel, mu, sigma)
    y_panel = panel["y"].values
    df = pd.read_csv(csv_path)
    out = {c: [] for c in ["ev_knn", "p_up", "p_big", "e_up", "tail_up", "downside",
                           "p5", "ev_ci_lo", "ev_ci_hi", "ev_n_features",
                           "ev_n_neighbors", "tail_ratio"]}
    for _, r in df.iterrows():
        feats = candidate_features(r.ticker)
        tr = tail_ratio(r.ticker, r) if feats else None
        if feats is None:
            for c in out: out[c].append(np.nan)
            continue
        frow = pd.DataFrame([feats])
        n_feats = int(frow[FEATURES].notna().sum(axis=1).iloc[0])
        if n_feats < MIN_FEATS_CAND:
            for c in out: out[c].append(np.nan)
            out["ev_n_features"][-1] = n_feats
            out["tail_ratio"][-1] = tr
            continue
        z = zmatrix(frow, mu, sigma)[0]
        d = masked_dist(z, Z_panel)
        finite = np.isfinite(d)
        if finite.sum() < MIN_NEIGHBORS:
            for c in out: out[c].append(np.nan)
            out["ev_n_features"][-1] = n_feats
            out["ev_n_neighbors"][-1] = int(finite.sum())
            out["tail_ratio"][-1] = tr
            continue
        kk = min(K, int(finite.sum()))
        nn = np.argpartition(d, kk-1)[:kk]
        y = y_panel[nn]
        m = ev_metrics(y)
        lo, hi = bootstrap_ci(y)
        for c in ["ev_knn", "p_up", "p_big", "e_up", "tail_up", "downside", "p5"]:
            out[c].append(m[c])
        out["ev_ci_lo"].append(lo); out["ev_ci_hi"].append(hi)
        out["ev_n_features"].append(n_feats)
        out["ev_n_neighbors"].append(kk)
        out["tail_ratio"].append(tr)
    for c, vals in out.items():
        df[c] = vals
    df["ev_ci_spans_zero"] = (df.ev_ci_lo <= 0) & (df.ev_ci_hi >= 0)
    df.to_csv(csv_path, index=False)
    return df


def walk_forward_validation(panel, k=K, save=True):
    p = panel.sort_values("event_date").reset_index(drop=True)
    y_all = p["y"].values
    evs, ys = [], []
    X = p[FEATURES].astype(float).values
    for i in range(MIN_PRIOR_EVENTS_WF, len(p)):
        prior = X[:i]
        mu = np.nanmean(prior, axis=0); sd = np.nanstd(prior, axis=0)
        sd = np.where(sd > 0, sd, 1.0)
        Zp = np.clip((prior - mu) / sd, -Z_CLIP, Z_CLIP)
        z = np.clip((X[i] - mu) / sd, -Z_CLIP, Z_CLIP)
        d = masked_dist(z, Zp)
        finite = np.isfinite(d)
        if finite.sum() < MIN_NEIGHBORS:
            continue
        kk = min(k, int(finite.sum()))
        nn = np.argpartition(d, kk-1)[:kk]
        evs.append(y_all[:i][nn].mean())
        ys.append(y_all[i])
    evs, ys = np.array(evs), np.array(ys)
    q = pd.qcut(evs, 5, labels=False, duplicates="drop")
    qmeans = [float(ys[q == i].mean()) for i in range(int(q.max())+1)]
    top, bot = ys[q == q.max()], ys[q == 0]
    diff = top.mean() - bot.mean()
    se = np.sqrt(top.var()/len(top) + bot.var()/len(bot))
    r = pd.Series(evs).rank().corr(pd.Series(ys).rank())
    t_sp = r*np.sqrt((len(evs)-2)/(1-r**2))
    res = {"n_scored": int(len(evs)), "quintile_means": qmeans,
           "spread_q5_q1": float(diff), "se": float(se),
           "passes_2se": bool(abs(diff) > 2*se),
           "spearman": round(float(r), 4), "spearman_t": round(float(t_sp), 2),
           "verdict": ("EV valida: quintil topo bate fundo (>2 SE)" if diff > 2*se
                       else ("ALERTA: spread NEGATIVO significativo — não publicar EV" if diff < -2*se
                             else "ordenação heurística, edge não provado (spread indistinguível de ruído)"))}
    if save:  # o selftest sintético NUNCA pode reescrever a validação de produção
        with open("output/ev_validation.json", "w") as f:
            json.dump(res, f, indent=1)
    return res


def selftest():
    """Painel sintético: feature 0 determina o sinal de y → topo tem de bater fundo."""
    rng = np.random.default_rng(0)
    n = 2000
    f0 = rng.normal(size=n)
    panel = pd.DataFrame({c: rng.normal(size=n) for c in FEATURES})
    panel["dist_52w_high"] = f0
    panel["y"] = np.where(f0 > 0, 0.1, -0.1) + rng.normal(0, 0.02, n)
    panel["event_date"] = [f"2020-{1+i%12:02d}-{1+i%28:02d}" for i in range(n)]
    res = walk_forward_validation(panel, save=False)
    assert res["spread_q5_q1"] > 0.05 and res["passes_2se"], f"selftest FALHOU: {res}"
    print(f"selftest OK: spread={res['spread_q5_q1']:.3f}, 2SE={res['passes_2se']}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    panel = load_panel()
    print(f"Painel: {len(panel)} eventos")
    if "--skip-validation" not in sys.argv:
        res = walk_forward_validation(panel)
        print(f"Walk-forward (n={res['n_scored']}): spread={res['spread_q5_q1']:+.4f} "
              f"(2SE={res['passes_2se']}), Spearman t={res['spearman_t']}")
        print(f"VEREDITO: {res['verdict']}")
        print(f"Quintis (EV crescente): {[f'{100*m:+.2f}%' for m in res['quintile_means']]}")
    df = score_candidates()
    el = df[(df.veto_v3.isna() | (df.veto_v3 == "")) & df.ev_knn.notna()]
    el = el[el.event_date.notna()].sort_values("ev_knn", ascending=False)
    print("\nTOP 15 por EV (não vetados):")
    cols = ["ticker", "event_date", "ev_knn", "p_up", "p_big", "e_up", "tail_up", "downside", "ev_ci_lo", "ev_ci_hi"]
    print(el[cols].head(15).to_string(index=False))
