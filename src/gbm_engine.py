# -*- coding: utf-8 -*-
"""v8→v10: GBM quantílico + conformal + meta-confiança calibrada + tribunal.

Regras na metodologia v8 (hiperparâmetros congelados; métricas primárias =
retorno realizado do TOP-1/TOP-3 por fold; limiar de abstenção 0,65) e v10
(braços A/B, cabeça p_up20_cal, precision@3/captura diárias, Gates 1/2/3).

Uso: .venv/bin/python -m src.gbm_engine [--tournament] [--tournament-v10] [--score]
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV

from . import config, ev_engine
from .factor_study import vix_on

FEATS = ev_engine.FEATURES + ["vix", "dow", "is_amc", "n_events_same_day"]
# v10 braço B: − log_mcap (look-ahead agrava a 10 anos) + nível de preço + liquidez $ PIT
FEATS_V10 = [f for f in FEATS if f != "log_mcap"] + ["log_close", "log_dollar_vol"]
FEATS = FEATS_V10  # ADOTADO — tribunal v10 2026-08-05, gates 1∧2∧3 (ver metodologia)
GBM_PARAMS = dict(max_iter=300, learning_rate=0.05, max_depth=4,
                  l2_regularization=1.0, random_state=42)
N_FOLDS = 30
MIN_TRAIN = 800
ABSTAIN_P = 0.65
BIG_UP = 0.05   # target da meta-confiança v8: subir >= +5%
P20_BUCKETS = [0, .02, .05, .10, .15, .20, .30, 1.0]


def _gbm_mean(X, y):
    m = HistGradientBoostingRegressor(loss="squared_error", **GBM_PARAMS)
    return m.fit(X, y)


def _gbm_quantile(X, y, q):
    m = HistGradientBoostingRegressor(loss="quantile", quantile=q, **GBM_PARAMS)
    return m.fit(X, y)


def _fit_calibrated(X, ybin):
    """Cabeça de probabilidade calibrada (isotónica, cv=3) — padrão v8."""
    if ybin.sum() < 30 or (1 - ybin).sum() < 30:
        return None
    clf = CalibratedClassifierCV(
        HistGradientBoostingClassifier(**GBM_PARAMS), method="isotonic", cv=3)
    return clf.fit(X, ybin)


def _wilson_lo(h, n, z=1.96):
    if not n:
        return None
    ph = h / n
    den = 1 + z * z / n
    ctr = ph + z * z / (2 * n)
    rad = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return float((ctr - rad) / den)


def _daily_top3(dates, probs, y, thr):
    """(picks, hits_nos_top3, positivos_totais) dos top-3 diários por prob."""
    df = pd.DataFrame({"d": dates, "p": probs, "y": y}).dropna(subset=["p"])
    picks = hits = pos_total = 0
    for _, g in df.groupby("d"):
        top = g.nlargest(3, "p")
        picks += len(top)
        hits += int((top.y >= thr).sum())
        pos_total += int((g.y >= thr).sum())
    return picks, hits, pos_total


def _calib_table(pairs, buckets):
    mp = pd.DataFrame(pairs, columns=["p", "hit"])
    if mp.empty:
        return []
    cut = pd.cut(mp.p, buckets)
    cal = mp.groupby(cut, observed=True).agg(n=("hit", "size"), previsto=("p", "mean"),
                                             realizado=("hit", "mean")).round(3)
    return [{"bucket": str(ix), "n": int(r.n), "previsto": float(r.previsto),
             "realizado": float(r.realizado)} for ix, r in cal.iterrows()]


def tournament(panel, feats=None, include_knn=True, out_path="output/gbm_validation.json"):
    """Walk-forward ancorado, N_FOLDS cronológicos. Métrica primária: retorno
    realizado do TOP-1/TOP-3 por fold. v10: cabeça p20 + métricas diárias."""
    feats = feats or FEATS
    p = panel.sort_values("event_date").reset_index(drop=True)
    X = p[feats].astype(float).values
    Xk = p[ev_engine.FEATURES].astype(float).values
    y = p["y"].values
    dates = p["event_date"].values
    n = len(p)
    fold_edges = np.linspace(MIN_TRAIN, n, N_FOLDS + 1).astype(int)

    res = {"gbm": {"top1": [], "top3": [], "all_pred": [], "all_real": []},
           "knn": {"top1": [], "top3": [], "all_pred": [], "all_real": []}}
    meta_pairs, meta_pairs20 = [], []
    d5 = {"picks": 0, "hits": 0, "pos": 0}    # top-3 diários por p_up5 (baseline captura)
    d20 = {"picks": 0, "hits": 0, "pos": 0}   # top-3 diários por p_up20
    n_test_total, n_pos20_total = 0, 0
    cover_hits, cover_n = 0, 0

    for f in range(N_FOLDS):
        a, b = fold_edges[f], fold_edges[f + 1]
        if b <= a:
            continue
        Xtr, ytr = X[:a], y[:a]
        Xte, yte = X[a:b], y[a:b]
        dte = dates[a:b]
        n_test_total += len(yte)
        n_pos20_total += int((yte >= config.BIG_UP20).sum())

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

        # meta-confiança v8: P(y>=+5%) calibrada no treino
        clf5 = _fit_calibrated(Xtr_f, (ytr >= BIG_UP).astype(int))
        if clf5 is not None:
            p_up5 = clf5.predict_proba(Xte_f)[:, 1]
            for pp, yy in zip(p_up5, yte):
                meta_pairs.append((float(pp), int(yy >= BIG_UP)))
            k, h, pos = _daily_top3(dte, p_up5, yte, config.BIG_UP20)
            d5["picks"] += k; d5["hits"] += h; d5["pos"] += pos

        # v10: cabeça moonshot P(y>=+20%) calibrada no treino
        clf20 = _fit_calibrated(Xtr_f, (ytr >= config.BIG_UP20).astype(int))
        if clf20 is not None:
            p_up20 = clf20.predict_proba(Xte_f)[:, 1]
            for pp, yy in zip(p_up20, yte):
                meta_pairs20.append((float(pp), int(yy >= config.BIG_UP20)))
            k, h, pos = _daily_top3(dte, p_up20, yte, config.BIG_UP20)
            d20["picks"] += k; d20["hits"] += h; d20["pos"] += pos

        # --- kNN (v7, mesmo harness; fora dos braços v10) ---
        if include_knn:
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
        if not r["top3"]:
            return None
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
                "top3_by_fold": [round(float(x), 4) for x in t3],
                "n_folds": len(t1),
                "quintile_means": [round(x, 4) for x in qm],
                "spread_q5_q1": round(float(diff), 4),
                "passes_2se": bool(abs(diff) > 2 * se),
                "spearman_t": round(float(t_sp), 2)}

    out = {"feats": feats, "gbm": summarize(res["gbm"]), "knn": summarize(res["knn"]),
           "conformal_coverage": round(cover_hits / cover_n, 3) if cover_n else None}

    # calibração P(>=+5%) por bucket + abstenção (v8)
    out["calibration"] = _calib_table(meta_pairs, [0, .3, .4, .5, .6, .65, .7, .8, 1.0])
    mp = pd.DataFrame(meta_pairs, columns=["p", "hit"])
    above = mp[mp.p >= ABSTAIN_P] if len(mp) else mp
    out["abstencao"] = {"limiar": ABSTAIN_P,
                        "pct_eventos_com_sinal": round(len(above) / len(mp), 3) if len(mp) else None,
                        "hit_rate_no_sinal": round(float(above.hit.mean()), 3) if len(above) else None}

    # v10: calibração e métricas diárias da cabeça p20
    out["calibration_20"] = _calib_table(meta_pairs20, P20_BUCKETS)
    base20 = n_pos20_total / n_test_total if n_test_total else None
    out["p20"] = {
        "base_rate_test": round(base20, 4) if base20 is not None else None,
        "n_test": n_test_total, "n_pos": n_pos20_total,
        "precision_at3_daily": round(d20["hits"] / d20["picks"], 4) if d20["picks"] else None,
        "precision_wilson_lo95": round(_wilson_lo(d20["hits"], d20["picks"]), 4) if d20["picks"] else None,
        "capture_daily": round(d20["hits"] / d20["pos"], 4) if d20["pos"] else None,
        "capture_daily_p5_baseline": round(d5["hits"] / d5["pos"], 4) if d5["pos"] else None,
        "picks": d20["picks"],
    }
    if out["knn"] is not None and out["gbm"] is not None:
        out["winner_top3"] = "gbm" if out["gbm"]["top3_mean"] >= out["knn"]["top3_mean"] else "knn"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    return out


def _print_summary(out):
    for eng in ["gbm", "knn"]:
        s = out.get(eng)
        if not s:
            continue
        print(f"  {eng.upper()}: TOP-1 {100*s['top1_mean']:+.2f}%±{100*s['top1_se']:.2f} | "
              f"TOP-3 {100*s['top3_mean']:+.2f}%±{100*s['top3_se']:.2f} | "
              f"spread {100*s['spread_q5_q1']:+.2f}pp (2SE={s['passes_2se']}) | t={s['spearman_t']}")
    print(f"  Cobertura conformal (alvo 0.80): {out['conformal_coverage']}")
    p20 = out["p20"]
    print(f"  p20: base {p20['base_rate_test']} | precision@3 {p20['precision_at3_daily']} "
          f"(Wilson-lo95 {p20['precision_wilson_lo95']}) | captura {p20['capture_daily']} "
          f"vs baseline p5 {p20['capture_daily_p5_baseline']}")


def gates_v10(outA, outB):
    """Gates pré-registados (metodologia v10 §8). Devolve dict com decisões."""
    t3A = np.array(outA["gbm"]["top3_by_fold"])
    t3B = np.array(outB["gbm"]["top3_by_fold"])
    m = min(len(t3A), len(t3B))
    diffs = t3B[:m] - t3A[:m]
    se = float(diffs.std() / np.sqrt(m)) if m else float("nan")
    gate1 = bool(diffs.mean() >= -se)
    winner = outB if gate1 else outA
    arm = "B" if gate1 else "A"

    p20 = winner["p20"]
    base = p20["base_rate_test"]
    g2a = (p20["capture_daily"] or 0) > (outA["p20"]["capture_daily_p5_baseline"] or 0)
    g2b = (p20["precision_wilson_lo95"] or 0) > (base if base is not None else 1)
    gate2 = bool(g2a and g2b)

    big = [c for c in winner["calibration_20"] if c["n"] >= 30]
    gate3 = bool(big) and all(0.5 * c["previsto"] <= c["realizado"] <= 2.0 * c["previsto"]
                              for c in big)
    return {"gate1_nao_regressao": gate1, "gate1_diff_media": round(float(diffs.mean()), 5),
            "gate1_se": round(se, 5), "braco_features": arm,
            "gate2_edge_moonshot": gate2, "gate2_captura_ok": bool(g2a), "gate2_wilson_ok": bool(g2b),
            "gate3_calibracao": gate3, "n_buckets_n30": len(big),
            "adota_features_B": gate1, "adota_cabeca_p20": bool(gate2 and gate3)}


def score_candidates(csv_path="output/candidatos.csv", feats=None):
    """Fit final no painel completo; aplica aos candidatos: gbm_ev, quantis
    conformal, p_up5_cal e p_up20_cal (v10)."""
    feats = feats or FEATS
    panel = ev_engine.load_panel().sort_values("event_date").reset_index(drop=True)
    X = panel[feats].astype(float).values
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
    clf5 = _fit_calibrated(Xf, (y >= BIG_UP).astype(int))
    clf20 = _fit_calibrated(Xf, (y >= config.BIG_UP20).astype(int))

    df = pd.read_csv(csv_path)
    day_counts = df.groupby("event_date")["ticker"].transform("count")
    df["_n_same_day"] = day_counts
    import datetime as dt
    vix_today = vix_on(dt.date.today().isoformat())
    rows = []
    for _, r in df.iterrows():
        cf = ev_engine.candidate_features(r.ticker)
        if cf is None or not r.event_date or pd.isna(r.event_date):
            rows.append([np.nan] * 8)
            continue
        try:
            dow = dt.date.fromisoformat(str(r.event_date)).weekday()
        except ValueError:
            dow = np.nan
        d = dict(cf)
        d.update({"vix": vix_today, "dow": dow,
                  "is_amc": 1 if r.get("timing") == "AMC" else 0,
                  "n_events_same_day": float(r.get("_n_same_day") or 0)})
        vec = [d.get(f) for f in feats]
        v = np.array([np.nan if x is None else float(x) for x in vec])
        v = np.where(np.isnan(v), med, v).reshape(1, -1)
        rows.append([float(gm.predict(v)[0]),
                     float(q10.predict(v)[0] - qhat),
                     float(q50.predict(v)[0]),
                     float(q90.predict(v)[0] + qhat),
                     float(clf5.predict_proba(v)[0, 1]) if clf5 is not None else np.nan,
                     float(clf20.predict_proba(v)[0, 1]) if clf20 is not None else np.nan,
                     1.0,
                     cf.get("log_dollar_vol") if cf.get("log_dollar_vol") is not None else np.nan])
    cols = ["gbm_ev", "gbm_q10", "gbm_q50", "gbm_q90", "p_up5_cal", "p_up20_cal", "gbm_scored",
            "log_dollar_vol"]
    for i, c in enumerate(cols):
        df[c] = [row[i] for row in rows]
    df.to_csv(csv_path, index=False)
    return df


if __name__ == "__main__":
    if "--tournament-v10" in sys.argv:
        panel = ev_engine.load_panel()
        print(f"TRIBUNAL v10 — painel {len(panel)} eventos "
              f"({panel.event_date.min()} → {panel.event_date.max()})")
        outA = tournament(panel, feats=FEATS, include_knn=False,
                          out_path="output/gbm_validation_v10A.json")
        print("Braço A (12 features v9):")
        _print_summary(outA)
        outB = tournament(panel, feats=FEATS_V10, include_knn=False,
                          out_path="output/gbm_validation_v10B.json")
        print("Braço B (13 = v9 − log_mcap + log_close + log_dollar_vol):")
        _print_summary(outB)
        g = gates_v10(outA, outB)
        print("\nGATES pré-registados (metodologia v10 §8):")
        print(f"  Gate 1 não-regressão: {'PASSA' if g['gate1_nao_regressao'] else 'FALHA'} "
              f"(diff média {100*g['gate1_diff_media']:+.3f}pp, SE {100*g['gate1_se']:.3f}pp) "
              f"→ features do braço {g['braco_features']}")
        print(f"  Gate 2 edge moonshot: {'PASSA' if g['gate2_edge_moonshot'] else 'FALHA'} "
              f"(captura>baseline: {g['gate2_captura_ok']}; Wilson>base: {g['gate2_wilson_ok']})")
        print(f"  Gate 3 calibração: {'PASSA' if g['gate3_calibracao'] else 'FALHA'} "
              f"({g['n_buckets_n30']} buckets com n≥30)")
        print(f"  DECISÃO: features B={'ADOTA' if g['adota_features_B'] else 'NÃO'} | "
              f"cabeça p20/Radar={'ADOTA' if g['adota_cabeca_p20'] else 'NÃO'}")
        with open("output/gates_v10.json", "w") as f:
            json.dump(g, f, indent=1)
    if "--tournament" in sys.argv or len(sys.argv) == 1:
        panel = ev_engine.load_panel()
        out = tournament(panel)
        print(f"TRIBUNAL ({out['gbm']['n_folds']} folds):")
        _print_summary(out)
        if "winner_top3" in out:
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
        print(el[["ticker", "event_date", "gbm_ev", "gbm_q10", "gbm_q90", "p_up5_cal", "p_up20_cal"]]
              .head(10).to_string(index=False))
