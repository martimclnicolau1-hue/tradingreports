# -*- coding: utf-8 -*-
"""v4: extração limpa do movimento de evento via term-structure de IV,
skew put-call e rácio O/S. + fator sandbagging (média das últimas 4 surpresas).

Matemática: TV_f = σf²·Tf e TV_b = σb²·Tb (variância total até cada expiração,
em anos). Var diária difusiva σd² = (TV_b−TV_f)/(Tb−Tf). Var do evento
σe² = TV_f − σd²·Tf. Movimento esperado |m| ≈ σe·√(2/π) (normal half-mean).
"""
import json, math, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yfinance as yf

def atm_iv(chain, spot):
    ivs = []
    for side in [chain.calls, chain.puts]:
        s = side.copy()
        s = s[(s.impliedVolatility > 0.01) & (s.impliedVolatility < 5)]
        if s.empty: continue
        s["d"] = (s.strike - spot).abs()
        ivs.append(float(s.sort_values("d").head(2).impliedVolatility.mean()))
    return np.mean(ivs) if ivs else None

def analyze(sym):
    t = yf.Ticker(sym)
    try:
        exps = t.options
        if not exps or len(exps) < 2: return {}
        spot = None
        for k in ("last_price", "lastPrice", "regularMarketPrice"):
            try:
                spot = t.fast_info.get(k) if hasattr(t.fast_info, "get") else None
            except Exception:
                spot = None
            if spot: break
        if not spot:
            h = t.history(period="5d")
            h = h[h["Close"].notna()]
            spot = float(h["Close"].iloc[-1]) if len(h) else None
        if not spot: return {}
        today = pd.Timestamp.today()
        e1, e2 = exps[0], exps[1]
        c1 = t.option_chain(e1); time.sleep(0.4)
        c2 = t.option_chain(e2); time.sleep(0.4)
        T1 = max((pd.Timestamp(e1)-today).days, 1)/365
        T2 = max((pd.Timestamp(e2)-today).days, 2)/365
        iv1, iv2 = atm_iv(c1, spot), atm_iv(c2, spot)
        out = {}
        if iv1 and iv2 and T2 > T1:
            tv1, tv2 = iv1**2*T1, iv2**2*T2
            sd2 = max((tv2-tv1)/(T2-T1), 0) / 252 * 365  # var difusiva/ano->por dia util aprox
            ev = tv1 - (tv2-tv1)/(T2-T1)*T1
            if ev > 0:
                out["clean_event_move"] = math.sqrt(ev)*math.sqrt(2/math.pi)
        # skew: IV do put ~5% OTM menos IV do call ~5% OTM (medo vs ganância)
        p = c1.puts.copy(); c = c1.calls.copy()
        p["d"] = (p.strike - spot*0.95).abs(); c["d"] = (c.strike - spot*1.05).abs()
        pv = p[(p.impliedVolatility>0.01)].sort_values("d").head(2).impliedVolatility.mean()
        cv = c[(c.impliedVolatility>0.01)].sort_values("d").head(2).impliedVolatility.mean()
        if pd.notna(pv) and pd.notna(cv): out["iv_skew_put_call"] = float(pv-cv)
        vol_opt = float(c1.calls.volume.fillna(0).sum() + c1.puts.volume.fillna(0).sum())
        out["opt_volume_front"] = vol_opt
        pcr = c1.puts.volume.fillna(0).sum() / max(c1.calls.volume.fillna(0).sum(), 1)
        out["put_call_vol_ratio"] = float(pcr)
        return out
    except Exception as e:
        print(f"  [WARN] {sym}: {e}")
        return {}

def sandbag(sym):
    try:
        df = pd.DataFrame(json.load(open(f"data/earnings_{sym}.json"))["data"])
        col = next((c for c in df.columns if "surprise" in c.lower()), None)
        s = pd.to_numeric(df[col], errors="coerce").dropna().head(4)
        return float(s.mean()) if len(s) >= 3 else None
    except Exception:
        return None

if __name__ == "__main__":
    df = pd.read_csv("output/candidatos.csv")
    import os
    if os.path.exists("data/optclean.json"):
        res = json.load(open("data/optclean.json"))
    else:
        res = {}
    # v11: carimbo asof — quotes do ÂMBITO (eventos ≤ T+2) refrescam diariamente;
    # o resto mantém a cache (staleness silenciosa era invisível antes)
    from datetime import date as _date, timedelta as _td
    hoje = _date.today().isoformat()
    cut = (_date.today() + _td(days=2)).isoformat()
    in_scope = set(df.loc[df.event_date.notna() & (df.event_date <= cut), "ticker"])
    for i, tkr in enumerate(df.ticker, 1):
        hit = res.get(tkr)
        if hit and (tkr not in in_scope or hit.get("asof") == hoje):
            continue
        print(f"[{i}/{len(df)}] {tkr}")
        r = analyze(tkr); r["sandbag_surprise_4q"] = sandbag(tkr); r["asof"] = hoje
        res[tkr] = r; time.sleep(0.3)
        json.dump(res, open("data/optclean.json","w"))
    for col in ["clean_event_move","iv_skew_put_call","put_call_vol_ratio","sandbag_surprise_4q"]:
        df[col] = df.ticker.map(lambda t: res[t].get(col))
    for c in ["clean_event_move","iv_skew_put_call","put_call_vol_ratio","sandbag_surprise_4q"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["edge_ratio_clean"] = (pd.to_numeric(df.avg_abs_move, errors="coerce")/df.clean_event_move).round(2)
    # score v4: direcional com pesos ∝|t| incl. sandbagging (t=1,37)
    def clip01(x): return max(0.0,min(1.0,x))
    def val(x, lo, hi):
        return 0.5 if x is None or (isinstance(x,float) and np.isnan(x)) else clip01((x-lo)/(hi-lo))
    def v4(r):
        direc = (0.33*val(r.dist_52w_high,-0.6,0)+0.22*val(r.rsi14,30,70)
                 +0.18*val(r.sandbag_surprise_4q,-10,40)+0.16*val(r.mom60,-0.3,0.3)
                 +0.09*val(r.skew_pct,-0.4,0.6)+0.02*val(r.beat_rate_8q,0.3,0.9))
        e = r.edge_ratio_clean if pd.notna(r.edge_ratio_clean) else r.edge_ratio
        return 100*(0.5*direc + 0.5*val(e,0.6,1.5))
    df["score_v4"] = df.apply(v4, axis=1).round(1)
    df.to_csv("output/candidatos.csv", index=False)
    top = df.dropna(subset=["event_date"]).sort_values("score_v4", ascending=False)
    print(top[["ticker","event_date","score_v3","score_v4","veto_v3","edge_ratio","edge_ratio_clean",
               "clean_event_move","iv_skew_put_call","sandbag_surprise_4q"]].head(16).to_string(index=False))
