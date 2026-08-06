# -*- coding: utf-8 -*-
"""Estudo de fatores point-in-time: o que previu a reação a earnings?

Painel: todos os (ticker, evento passado) com >=4 eventos de história.
Fatores calculados APENAS com informação disponível ANTES de cada evento.
Regra de re-ponderação registada ANTES de correr (ver metodologia.md v3):
pesos direcionais proporcionais a |t|; snapshot fundamental = veto, não peso.
"""
import glob, json, os, time
import numpy as np, pandas as pd

from .reactions import event_reactions

_VIX = None
def vix_on(date_str):
    """Fecho do ^VIX no dia (ou último anterior). Cache em data/vix.csv;
    refetch se o ficheiro tiver >5 dias (senão o VIX do scoring ficava fóssil)."""
    global _VIX
    if _VIX is None:
        p = "data/vix.csv"
        stale = os.path.exists(p) and (time.time() - os.path.getmtime(p)) > 5*86400
        if not os.path.exists(p) or stale:
            try:
                from . import fetch
                h = fetch.get_ticker("^VIX").history(period="10y")
                h[["Close"]].to_csv(p)
            except Exception:
                _VIX = False
                return None
        v = pd.read_csv(p, index_col=0)
        v.index = pd.to_datetime(v.index, utc=True, errors="coerce").tz_localize(None).normalize()
        _VIX = v["Close"]
    if _VIX is False:
        return None
    try:
        d = pd.Timestamp(date_str)
        s = _VIX[_VIX.index <= d]
        return float(s.iloc[-1]) if len(s) else None
    except Exception:
        return None

def load_earnings(sym):
    p = f"data/earnings_{sym}.json"
    if not os.path.exists(p): return None
    df = pd.DataFrame(json.load(open(p))["data"])
    if df.empty: return None
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df

def load_prices(sym):
    p = f"data/prices_{sym}.csv"
    if not os.path.exists(p): return None
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
    df = df[df.index.notna()]
    return df[df["Close"].notna()]

def features_from_history(closes_pre, vols_pre, hist_reactions, hist_surprises, log_mcap):
    """Features point-in-time usadas TANTO no painel como nos candidatos de hoje
    (paridade obrigatória — metodologia v7). hist_* do mais recente p/ o mais antigo."""
    hr = np.array(hist_reactions, dtype=float)
    hs = [s for s in hist_surprises if s is not None]
    mom60 = closes_pre[-1]/closes_pre[-61]-1 if len(closes_pre) > 61 else None
    d52 = closes_pre[-1]/closes_pre[-252:].max()-1 if len(closes_pre) >= 252 else None
    delta = np.diff(closes_pre[-15:]); g = delta[delta > 0].sum(); l = -delta[delta < 0].sum()
    rsi = 100*g/(g+l) if (g+l) > 0 else None
    relvol = None
    if vols_pre is not None and len(vols_pre) >= 65:
        v60 = np.nanmean(vols_pre[-65:-5]); v5 = np.nanmean(vols_pre[-5:])
        if v60 and v60 > 0:
            relvol = float(v5/v60)
    # v10: nível de preço (efeito lottery) e liquidez $ point-in-time
    log_close = float(np.log10(closes_pre[-1])) if closes_pre[-1] > 0 else None
    ldv = None
    if vols_pre is not None and len(vols_pre) >= 20:
        dv = np.nanmean(np.asarray(closes_pre[-20:]) * np.asarray(vols_pre[-20:], dtype=float))
        if np.isfinite(dv) and dv > 0:
            ldv = float(np.log10(dv))
    return {
        "prior_beat_rate": float(np.mean([s > 0 for s in hs])) if len(hs) >= 4 else None,
        "prior_skew": float((hr >= .10).mean() - (hr <= -.10).mean()),
        "prior_up_big_rate": float((hr >= .10).mean()),
        "prior_avg_move": float(np.abs(hr).mean()),
        "sandbag": float(np.mean(hs[:4])) if len(hs) >= 3 else None,
        "mom60": mom60, "dist_52w_high": d52, "rsi14": rsi,
        "log_mcap": log_mcap, "rel_volume": relvol,
        "log_close": log_close, "log_dollar_vol": ldv,
    }


def _log_mcap(sym):
    try:
        mc = json.load(open(f"data/info_{sym}.json"))["data"].get("marketCap")
        return float(np.log10(mc)) if mc and mc > 0 else None
    except Exception:
        return None


def build_panel():
    rows = []
    n_bad_y = 0
    for p in glob.glob("data/prices_*.csv"):
        sym = p.split("prices_")[1][:-4]
        edf, prices = load_earnings(sym), load_prices(sym)
        if edf is None or prices is None or len(prices) < 260: continue
        scol = next((c for c in edf.columns if "surprise" in c.lower()), None)
        idx = prices.index.tz_localize(None).normalize()
        closes = prices["Close"].values
        volumes = prices["Volume"].values if "Volume" in prices else None
        lm = _log_mcap(sym)
        events = [e if e["i_before"] >= 60 else None for e in event_reactions(edf, prices)]
        for k in range(len(events)-4):  # precisa de >=4 eventos de história (k+1..fim)
            ev = events[k]
            if ev is None: continue
            # v13: limiar parametrizado (braço B do tribunal usa EVENTCAL_YMAX=2.0);
            # entre 1,0 e YMAX só entra com guarda de sanidade (preço/volume válidos
            # nos 2 dias — apanha artefactos de dados sem matar movers reais >100%)
            y_max = float(os.environ.get("EVENTCAL_YMAX", "2.0"))  # v13 ADOTADO 2026-08-06
            ay = abs(ev["reaction"])
            if ay > y_max:
                print(f"[build_panel] descartado |y|>{y_max}: {sym} {ev['date']} y={ev['reaction']:+.2f}")
                n_bad_y += 1; continue
            if ay > 1.0:
                b_ = ev["i_before"]
                guard = (closes[b_] > 0.5 and b_ + 1 < len(closes) and closes[b_ + 1] > 0.5
                         and (volumes is None or (volumes[b_] > 0 and volumes[b_ + 1] > 0)))
                if not guard:
                    print(f"[build_panel] descartado |y|>1 SEM guarda: {sym} {ev['date']} y={ev['reaction']:+.2f}")
                    n_bad_y += 1; continue
            hist = [e for e in events[k+1:] if e is not None]
            if len(hist) < 4: continue
            b = ev["i_before"]
            feats = features_from_history(
                closes[:b+1], volumes[:b+1] if volumes is not None else None,
                [h["reaction"] for h in hist], [h["surprise"] for h in hist], lm)
            import datetime as _dt
            row = {"ticker": sym, "event_date": ev["date"], "y": ev["reaction"],
                   "abs_y": abs(ev["reaction"]), "surprise_at_k": ev["surprise"],
                   "vix": vix_on(ev["date"]),
                   "dow": _dt.date.fromisoformat(ev["date"]).weekday(),
                   "is_amc": int(ev.get("amc", True))}
            row.update(feats)
            rows.append(row)
    if n_bad_y:
        print(f"[build_panel] descartados {n_bad_y} eventos com |y|>1,0 (erros de dados)")
    df = pd.DataFrame(rows)
    if not df.empty:
        df["n_events_same_day"] = df.groupby("event_date")["ticker"].transform("count")
        # v12: features FINRA (PIT, keyed na data do ficheiro) — merge declarado v12§2
        try:
            from . import finra_short
            if os.path.exists(finra_short.DATA):
                df = finra_short.attach_features(df)
                print(f"[build_panel] FINRA: short_ratio_z5 cobre "
                      f"{df.short_ratio_z5.notna().mean():.0%} dos eventos")
        except Exception as e:
            print(f"[build_panel] FINRA indisponível ({e}) — painel sem short_ratio_*")
    return df

def tstat(df, x, y):
    d = df[[x, y]].dropna()
    n = len(d)
    if n < 30: return n, None, None
    r = d[x].rank().corr(d[y].rank())  # Spearman = Pearson sobre ranks (sem scipy)
    t = r*np.sqrt((n-2)/(1-r**2))
    return n, round(r, 3), round(t, 2)

if __name__ == "__main__":
    panel = build_panel()
    print(f"Painel: {len(panel)} eventos, {panel.ticker.nunique()} tickers\n")
    print("=== FATORES DIRECIONAIS (preveem o SINAL da reação y) ===")
    for f in ["prior_beat_rate", "prior_skew", "mom60", "dist_52w_high", "rsi14"]:
        n, r, t = tstat(panel, f, "y")
        sig = " <-- SIGNIFICATIVO" if t and abs(t) >= 2 else ""
        print(f"  {f:18s} n={n:4d} spearman={r} t={t}{sig}")
    print("\n=== MECANISMO (só conhecido APÓS o print — não negociável ex-ante) ===")
    n, r, t = tstat(panel, "surprise_at_k", "y")
    print(f"  surprise_at_k      n={n:4d} spearman={r} t={t}")
    print("\n=== FATOR DE VOLATILIDADE (prevê o TAMANHO |y|) ===")
    n, r, t = tstat(panel, "prior_avg_move", "abs_y")
    sig = " <-- SIGNIFICATIVO" if t and abs(t) >= 2 else ""
    print(f"  prior_avg_move     n={n:4d} spearman={r} t={t}{sig}")
    panel.to_csv("output/factor_panel.csv", index=False)
    print("\nGuardado: output/factor_panel.csv")
