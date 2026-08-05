# -*- coding: utf-8 -*-
"""v8: GBM quantílico + conformal + meta-confiança calibrada + tribunal vs kNN.

Regras na metodologia v8 (hiperparâmetros congelados; métricas primárias =
retorno realizado do TOP-1/TOP-3 por fold; limiar de abstenção 0,65).

Uso: .venv/bin/python -m src.gbm_engine [--tournament] [--score]
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression

from . import config, ev_engine
from .factor_study import vix_on

FEATS = ev_engine.FEATURES + ["vix", "dow", "is_amc", "n_events_same_day"]
GBM_PARAMS = dict(max_iter=300, learning_rate=0.05, max_depth=4,
                  l2_regularization=1.0, random_state=42)
N_FOLDS = 30
MIN_TRAIN = 800
ABSTAIN_P = 0.65
BIG_UP = 0.05  # target do meta-modelo: subir >= +5%


def _gbm_mean(X, y):
    m = HistGradientBoostingRegressor(loss="squared_error", **GBM_PARAMS)
    return m.fit(X, y)


def _gbm_quantile(X, y, q):
    m = HistGradientBoostingRegressor(loss="quantile", quantile=q, **GBM_PARAMS)
    return m.fit(X, y)


def _clf(X, y):
    base = HistGradientBoostingClassifier(**GBM_PARAMS)
    return base.fit(X, y)


def tournament(panel):
    """Walk-forward ancorado, N_FOLDS cronológicos: kNN v7 vs GBM v8.
    Métrica primária: retorno realizado do TOP-1/TOP-3 escolhidos em cada fold."""
    p = panel.sort_values("event_date").reset_index(drop=True)
    X = p[FEATS].astype(float).values
    Xk = p[ev_engine.FEATURES].astype(float).values
    y = p["y"].values
    n = len(p)
    fold_edges = np.linspace(MIN_TRAIN, n, N_FOLDS + 1).astype(int)

    res = {"gbm": {"top1": [], "top3": [], "all_pred": [], "all_real": []},
           "knn": {"top1": [], "top3": [], "all_pred": [], "all_real": []}}
    meta_pairs = []  # (p_calibrada_prevista, outcome) para curva de calibração
    cover_hits, cover_n = 0, 0

    for f in range(N_FOLDS):
        a, b = fold_edges[f], fold_edges[f + 1]
        if b <= a:
            continue
        Xtr, ytr = X[:a], y[:a]
        Xte, yte = X[a:b], y[a:b]

        # --- GBM ---
        med = np.nanmedian(Xtr, axis=0)
        Xtr_f = np.where(np.isnan(Xtr), med, Xtr)
        Xte_f = np.where(np.isnan(Xte), med, Xte)
        gm = _gbm_mean(Xtr_f, ytr)
        pred = gm.predict(Xte_f)
        order = np.argsort(pred)[::-1]
        res["gbm"]["top1"].append(float(yte[order[0]]))
        res["gbm"]["top3"].append(float(yte[order[:3]].mean()))
        res["gbm"]["all_pred"] += list(pred)
        res["gbm"]["all_real"] += list(yte)

        # conformal split dentro do treino (últimos 20% como calibração)
        cal_cut = int(0.8 * a)
        q10 = _gbm_quantile(Xtr_f[:cal_cut], ytr[:cal_cut], 0.1)
        q90 = _gbm_quantile(Xtr_f[:cal_cut], ytr[:cal_cut], 0.9)
        Xcal = Xtr_f[cal_cut:]; ycal = ytr[cal_cut:]
        lo_c, hi_c = q10.predict(Xcal), q90.predict(Xcal)
        scores = np.maximum(lo_c - ycal, ycal - hi_c)
        qhat = np.quantile(scores, 0.8)
        lo, hi = q10.predict(Xte_f) - qhat, q90.predict(Xte_f) + qhat
        cover_hits += int(((yte >= lo) & (yte <= hi)).sum())
        cover_n += len(yte)

        # meta-confiança: classificador P(y>=+5%) calibrado no treino
        ybin = (ytr >= BIG_UP).astype(int)
        if ybin.sum() >= 30 and (1 - ybin).sum() >= 30:
            clf = CalibratedClassifierCV(
                HistGradientBoostingClassifier(**GBM_PARAMS), method="isotonic", cv=3)
            clf.fit(Xtr_f, ybin)
            p_up5 = clf.predict_proba(Xte_f)[:, 1]
            for pp, yy in zip(p_up5, yte):
                meta_pairs.append((float(pp), int(yy >= BIG_UP)))

        # --- kNN (v7, mesmo harness) ---
        mu = np.nanmean(Xk[:a], axis=0); sd = np.nanstd(Xk[:a], axis=0)
        sd = np.where(sd > 0, sd, 1.0)
        Ztr = np.clip((Xk[:a] - mu) / sd, -3, 3)
        preds_k = []
        for i in range(a, b):
            z = np.clip((Xk[i] - mu) / sd, -3, 3)
            d = ev_engine.masked_dist(z, Ztr)
            finite = np.isfinite(d)
            if finite.sum() < ev_engine.MIN_NEIGHBORS:
                preds_k.append(np.nan); continue
            kk = min(ev_engine.K, int(finite.sum()))
            nn = np.argpartition(d, kk - 1)[:kk]
            preds_k.append(float(y[:a][nn].mean()))
        preds_k = np.array(preds_k)
        ok = ~np.isnan(preds_k)
        if ok.sum() >= 3:
            order_k = np.argsort(np.where(ok, preds_k, -np.inf))[::-1]
            res["knn"]["top1"].append(float(yte[order_k[0]]))
            res["knn"]["top3"].append(float(yte[order_k[:3]].mean()))
        res["knn"]["all_pred"] += list(preds_k)
        res["knn"]["all_real"] += list(yte)

    def summarize(r):
        t1, t3 = np.array(r["top1"]), np.array(r["top3"])
        pred = np.array(r["all_pred"]); real = np.array(r["all_real"])
        ok = ~np.isnan(pred)
        sp = pd.Series(pred[ok]).rank().corr(pd.Series(real[ok]).rank())
        t_sp = sp * np.sqrt((ok.sum() - 2) / (1 - sp ** 2))
        q = pd.qcut(pd.Series(pred[ok]), 5, labels=False, duplicates="drop")
        qm = [float(real[ok][q == i].mean()) for i in range(int(q.max()) + 1)]
        top, bot = real[ok][q == q.max()], real[ok][q == 0]
        diff = top.mean() - bot.mean()
        se = np.sqrt(top.var() / len(top) + bot.var() / len(bot))
        return {"top1_mean": round(float(t1.mean()), 4),
                "top1_se": round(float(t1.std() / np.sqrt(len(t1))), 4),
                "top3_mean": round(float(t3.mean()), 4),
                "top3_se": round(float(t3.std() / np.sqrt(len(t3))), 4),
                "n_folds": len(t1),
                "quintile_means": [round(x, 4) for x in qm],
                "spread_q5_q1": round(float(diff), 4),
                "passes_2se": bool(abs(diff) > 2 * se),
                "spearman_t": round(float(t_sp), 2)}

    out = {"gbm": summarize(res["gbm"]), "knn": summarize(res["knn"]),
           "conformal_coverage": round(cover_hits / cover_n, 3) if cover_n else None}

    # curva de calibração P(>=+5%) por bucket
    mp = pd.DataFrame(meta_pairs, columns=["p", "hit"])
    buckets = pd.cut(mp.p, [0, .3, .4, .5, .6, .65, .7, .8, 1.0])
    cal = mp.groupby(buckets, observed=True).agg(n=("hit", "size"), previsto=("p", "mean"),
                                                realizado=("hit", "mean")).round(3)
    out["calibration"] = [
        {"bucket": str(ix), "n": int(r.n), "previsto": float(r.previsto),
         "realizado": float(r.realizado)} for ix, r in cal.iterrows()]
    # taxa de sinal e hit-rate acima do limiar de abstenção
    above = mp[mp.p >= ABSTAIN_P]
    out["abstencao"] = {"limiar": ABSTAIN_P,
                        "pct_eventos_com_sinal": round(len(above) / len(mp), 3) if len(mp) else None,
                        "hit_rate_no_sinal": round(float(above.hit.mean()), 3) if len(above) else None}
    winner = "gbm" if out["gbm"]["top3_mean"] >= out["knn"]["top3_mean"] else "knn"
    out["winner_top3"] = winner
    with open("output/gbm_validation.json", "w") as f:
        json.dump(out, f, indent=1)
    return out


def score_candidates(csv_path="output/candidatos.csv"):
    """Fit final no painel completo; aplica aos candidatos: gbm_ev, quantis
    conformal, p_up5_cal (confiança calibrada)."""
    panel = ev_engine.load_panel().sort_values("event_date").reset_index(drop=True)
    X = panel[FEATS].astype(float).values
    y = panel["y"].values
    med = np.nanmedian(X, axis=0)
    Xf = np.where(np.isnan(X), med, X)
    cut = int(0.8 * len(Xf))
    gm = _gbm_mean(Xf, y)
    q10 = _gbm_quantile(Xf[:cut], y[:cut], 0.1)
    q50 = _gbm_quantile(Xf[:cut], y[:cut], 0.5)
    q90 = _gbm_quantile(Xf[:cut], y[:cut], 0.9)
    scores = np.maximum(q10.predict(Xf[cut:]) - y[cut:], y[cut:] - q90.predict(Xf[cut:]))
    qhat = float(np.quantile(scores, 0.8))
    clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**GBM_PARAMS),
                                 method="isotonic", cv=3)
    clf.fit(Xf, (y >= BIG_UP).astype(int))

    df = pd.read_csv(csv_path)
    day_counts = df.groupby("event_date")["ticker"].transform("count")
    df["_n_same_day"] = day_counts
    import datetime as dt
    vix_today = vix_on(dt.date.today().isoformat())
    rows = []
    for _, r in df.iterrows():
        feats = ev_engine.candidate_features(r.ticker)
        if feats is None or not r.event_date or pd.isna(r.event_date):
            rows.append([np.nan] * 6)
            continue
        try:
            dow = dt.date.fromisoformat(str(r.event_date)).weekday()
        except ValueError:
            dow = np.nan
        vec = [feats.get(f) for f in ev_engine.FEATURES] + \
              [vix_today, dow, 1 if r.get("timing") == "AMC" else 0,
               float(r.get("_n_same_day") or 0)]
        v = np.array([np.nan if x is None else float(x) for x in vec])
        v = np.where(np.isnan(v), med, v).reshape(1, -1)
        rows.append([float(gm.predict(v)[0]),
                     float(q10.predict(v)[0] - qhat),
                     float(q50.predict(v)[0]),
                     float(q90.predict(v)[0] + qhat),
                     float(clf.predict_proba(v)[0, 1]),
                     1.0])
    cols = ["gbm_ev", "gbm_q10", "gbm_q50", "gbm_q90", "p_up5_cal", "gbm_scored"]
    for i, c in enumerate(cols):
        df[c] = [row[i] for row in rows]
    df.to_csv(csv_path, index=False)
    return df


if __name__ == "__main__":
    if "--tournament" in sys.argv or len(sys.argv) == 1:
        panel = ev_engine.load_panel()
        out = tournament(panel)
        print(f"TRIBUNAL ({out['gbm']['n_folds']} folds):")
        for eng in ["gbm", "knn"]:
            s = out[eng]
            print(f"  {eng.upper()}: TOP-1 {100*s['top1_mean']:+.2f}%±{100*s['top1_se']:.2f} | "
                  f"TOP-3 {100*s['top3_mean']:+.2f}%±{100*s['top3_se']:.2f} | "
                  f"spread {100*s['spread_q5_q1']:+.2f}pp (2SE={s['passes_2se']}) | t={s['spearman_t']}")
        print(f"  Cobertura conformal (alvo 0.80): {out['conformal_coverage']}")
        print(f"  Vencedor TOP-3: {out['winner_top3'].upper()}")
        print(f"  Abstenção: sinal em {out['abstencao']['pct_eventos_com_sinal']} dos eventos; "
              f"hit-rate no sinal: {out['abstencao']['hit_rate_no_sinal']}")
        print("  Calibração P(>=+5%):")
        for c in out["calibration"]:
            print(f"    {c['bucket']}: previsto {c['previsto']:.2f} vs realizado {c['realizado']:.2f} (n={c['n']})")
    if "--score" in sys.argv or len(sys.argv) == 1:
        df = score_candidates()
        el = df[(df.veto_v3.isna() | (df.veto_v3 == "")) & df.gbm_ev.notna() & df.event_date.notna()]
        el = el.sort_values("gbm_ev", ascending=False)
        print("\nTOP 10 GBM (não vetados):")
        print(el[["ticker", "event_date", "gbm_ev", "gbm_q10", "gbm_q90", "p_up5_cal"]]
              .head(10).to_string(index=False))
