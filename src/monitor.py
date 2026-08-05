# -*- coding: utf-8 -*-
"""v12-A3/A5: indicador de regime + monitor de tripwires (metodologia v12§3-4).

Tripwires (limiares FIXOS pré-registados) — o sistema só está "avariado" se:
 (a) DESCALIBRAÇÃO: bucket de calibração com n≥30 e realizado fora de
     [0,5×; 2×] do previsto;
 (b) LIFT MORTO: precision@3 da cabeça p20 ≤ 1,0× a taxa-base;
 (c) ESPINHA MORTA: TOP-3 realizado ≤ 0 em 2 corridas mensais consecutivas;
 (d) COBERTURA conformal fora de [0,75; 0,85].
Perder picks individuais NÃO é tripwire — é a lotaria declarada.

Regime (contexto, zero peso): % dos últimos 50 eventos do painel com |y| acima
da mediana dos 4 eventos anteriores do próprio ticker. >0,50 = COMPRADOR
(moves grandes vs hábito); <0,42 = VENDEDOR (baseline estrutural 58/42).

Uso: .venv/bin/python -m src.monitor  → output/monitor.json (+ histórico jsonl)
"""
import json
import os
from datetime import date

import pandas as pd

HIST = "output/monitor_history.jsonl"


def regime(panel_path="output/factor_panel.csv", n=50):
    try:
        p = pd.read_csv(panel_path, usecols=["ticker", "event_date", "y", "prior_avg_move"])
    except Exception:
        return None
    p = p.dropna(subset=["y"]).sort_values("event_date")
    # |y| acima do hábito próprio: prior_avg_move é a média |reação| dos eventos
    # anteriores do ticker (PIT, já no painel) — proxy da mediana móvel pré-registada
    tail = p.tail(n).dropna(subset=["prior_avg_move"])
    if len(tail) < 30:
        return None
    frac = float((tail.y.abs() > tail.prior_avg_move).mean())
    label = "COMPRADOR" if frac > 0.50 else ("VENDEDOR" if frac < 0.42 else "NEUTRO")
    return {"frac_acima_habito": round(frac, 3), "n": len(tail),
            "ate": tail.event_date.max(), "label": label}


def tripwires():
    out = {"checked_at": date.today().isoformat(), "tripped": [], "ok": []}
    val = {}
    if os.path.exists("output/gbm_validation.json"):
        val = json.load(open("output/gbm_validation.json"))

    # (a) descalibração — buckets p5 e p20 com n>=30
    bad = []
    for key in ("calibration", "calibration_20"):
        for c in val.get(key, []):
            if c["n"] >= 30 and c["previsto"] > 0 and not \
                    (0.5 * c["previsto"] <= c["realizado"] <= 2.0 * c["previsto"]):
                bad.append(f"{key}:{c['bucket']} previu {c['previsto']:.2f} "
                           f"realizou {c['realizado']:.2f} (n={c['n']})")
    out["tripped" if bad else "ok"].append(
        {"tripwire": "descalibracao", "detalhe": bad or "todos os buckets n≥30 dentro de [0,5×;2×]"})

    # (b) lift morto
    p20 = val.get("p20", {})
    prec, base = p20.get("precision_at3_daily"), p20.get("base_rate_test")
    if prec is not None and base:
        lift = prec / base
        (out["tripped"] if lift <= 1.0 else out["ok"]).append(
            {"tripwire": "lift_morto", "detalhe": f"precision@3 {prec:.3f} / base {base:.3f} = {lift:.2f}×"})

    # (c) espinha morta — 2 corridas mensais consecutivas com TOP-3 <= 0
    top3 = (val.get("gbm") or {}).get("top3_mean")
    hist = []
    if os.path.exists(HIST):
        hist = [json.loads(l) for l in open(HIST) if l.strip()]
    prev = hist[-1].get("top3_mean") if hist else None
    dead = top3 is not None and top3 <= 0 and prev is not None and prev <= 0
    (out["tripped"] if dead else out["ok"]).append(
        {"tripwire": "espinha_morta",
         "detalhe": f"TOP-3 atual {top3} | anterior {prev} (precisa 2 consecutivos ≤0)"})

    # (d) cobertura conformal
    cov = val.get("conformal_coverage")
    if cov is not None:
        (out["tripped"] if not (0.75 <= cov <= 0.85) else out["ok"]).append(
            {"tripwire": "cobertura", "detalhe": f"{cov} vs alvo [0,75; 0,85]"})

    out["any_tripped"] = bool(out["tripped"])
    out["regime"] = regime()
    with open("output/monitor.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    with open(HIST, "a") as f:
        f.write(json.dumps({"date": out["checked_at"], "top3_mean": top3,
                            "coverage": cov, "any_tripped": out["any_tripped"]}) + "\n")
    return out


if __name__ == "__main__":
    r = tripwires()
    print(f"Tripwires: {'⚠ DISPARADOS: ' + str([t['tripwire'] for t in r['tripped']]) if r['any_tripped'] else 'todos verdes ✓'}")
    if r.get("regime"):
        print(f"Regime: {r['regime']['label']} ({r['regime']['frac_acima_habito']:.0%} dos últimos "
              f"{r['regime']['n']} eventos acima do hábito próprio, até {r['regime']['ate']})")
