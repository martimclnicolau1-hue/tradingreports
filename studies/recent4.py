# -*- coding: utf-8 -*-
"""Comparação com regime recente (últimos 4 reports) + classificação AI-proof.
AI_CLASS qualitativa e editável: 'IA' = vende IA/beneficiária direta;
'FISICO' = não substituível por IA (físico/regulado/biologia);
'EXPOSTO' = software/serviço que a IA pode comoditizar -> excluído."""
import numpy as np, pandas as pd
from src.factor_study import load_earnings, load_prices

AI_CLASS = {
 "LLY":"FISICO","NVO":"FISICO","OSCR":"FISICO","CELH":"FISICO","MELI":"FISICO",
 "EXPE":"EXPOSTO","TPR":"FISICO","DIS":"EXPOSTO","ABNB":"EXPOSTO","UBER":"FISICO",
 "DASH":"FISICO","SNAP":"EXPOSTO","PINS":"EXPOSTO","RDDT":"EXPOSTO","HOOD":"EXPOSTO",
 "CVNA":"FISICO","ANET":"IA","FTNT":"IA","ARM":"IA","TTWO":"EXPOSTO","EA":"EXPOSTO",
 "ZG":"EXPOSTO","W":"FISICO","ETSY":"FISICO","RL":"FISICO","DE":"FISICO","BABA":"FISICO",
 "BIDU":"IA","NTES":"EXPOSTO","TME":"EXPOSTO","SONY":"FISICO","AKAM":"IA","GDDY":"EXPOSTO",
 "BILL":"EXPOSTO","MNST":"FISICO","SWKS":"IA","MTCH":"EXPOSTO","YELP":"EXPOSTO","TDOC":"EXPOSTO",
  "APP":"IA","INOD":"IA","SMCI":"IA","NBIS":"IA","CRWV":"IA","COHR":"IA","LITE":"IA",
 "AAOI":"IA","AMAT":"IA","CSCO":"IA","SITM":"IA","IONQ":"IA","OKLO":"IA","WULF":"IA","CLSK":"IA",
 "AXON":"FISICO","BROS":"FISICO","SHAK":"FISICO","CAVA":"FISICO","ONON":"FISICO","SG":"FISICO",
 "MRNA":"FISICO","NVAX":"FISICO","SRPT":"FISICO","LNTH":"FISICO","IMVT":"FISICO",
 "SE":"FISICO","JD":"FISICO","DLO":"FISICO","STNE":"FISICO","ASTS":"FISICO","RKLB":"FISICO",
 "LUNR":"FISICO","MARA":"IA","RIOT":"IA","SHOP":"EXPOSTO","DUOL":"EXPOSTO","FROG":"EXPOSTO",
 "TTD":"EXPOSTO","DDOG":"IA","NET":"IA","TWLO":"EXPOSTO","TEAM":"EXPOSTO","U":"EXPOSTO",
 "GDRX":"EXPOSTO","HIMS":"EXPOSTO","FUBO":"EXPOSTO","PTON":"FISICO","LYFT":"FISICO","MNDY":"EXPOSTO","OKLO":"IA",
}

def last4(sym):
    edf, pr = load_earnings(sym), load_prices(sym)
    if edf is None or pr is None: return None
    idx = pr.index.tz_localize(None).normalize(); c = pr["Close"].values
    now = pd.Timestamp.utcnow().tz_localize(None)
    past = edf[edf["date"].dt.tz_localize(None) < now].head(4)
    out = []
    for _, r in past.iterrows():
        ts = r["date"].tz_convert("America/New_York")
        amc = ts.hour >= 16 or ts.hour == 0
        day = pd.Timestamp(ts.date()); pos = idx.searchsorted(day)
        b, a = (pos, pos+1) if amc else (pos-1, pos)
        if b < 0 or a >= len(c): continue
        out.append(c[a]/c[b]-1)
    return out if len(out) == 4 else None

df = pd.read_csv("output/candidatos.csv").dropna(subset=["event_date"])
df = df[df.veto_v3.isna() | (df.veto_v3 == "")]
rows = []
for _, r in df.iterrows():
    cls = AI_CLASS.get(r.ticker, "?")
    if cls == "EXPOSTO": continue
    r4 = last4(r.ticker)
    if r4 is None: continue
    imp = r.clean_event_move if pd.notna(r.clean_event_move) else r.implied_move_pct
    avg4 = np.mean(np.abs(r4))
    rows.append({"dia": r.event_date, "ticker": r.ticker, "classe": cls,
                 "ultimos4": " / ".join(f"{x:+.0%}" for x in r4),
                 "media4": f"{np.mean(r4):+.1%}", "subidas4": sum(x > 0 for x in r4),
                 "edge_recente": round(avg4/imp, 2) if imp and imp > 0 else None,
                 "v4": r.score_v4})
out = pd.DataFrame(rows).sort_values(["dia", "v4"], ascending=[True, False])
print(out.to_string(index=False))
