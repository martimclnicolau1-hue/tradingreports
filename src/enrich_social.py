# -*- coding: utf-8 -*-
"""Enriquecimento social pós-run: ApeWisdom (mentions Reddit agregadas).
Corre depois do run.py: .venv/bin/python -m src.enrich_social
Junta colunas ao candidatos.csv e acrescenta secção ao calendario.md.
CONTEXTO, não score (decisão pré-registada na metodologia v2)."""
import time
import pandas as pd
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_apewisdom(pages=8):
    out = {}
    for p in range(1, pages + 1):
        try:
            r = requests.get(f"https://apewisdom.io/api/v1.0/filter/all-stocks/page/{p}",
                             headers=HEADERS, timeout=20)
            r.raise_for_status()
            for row in r.json().get("results", []):
                out[row["ticker"]] = {
                    "reddit_rank": row.get("rank"),
                    "reddit_mentions": row.get("mentions"),
                    "reddit_mentions_24h_ago": row.get("mentions_24h_ago"),
                }
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] ApeWisdom p{p}: {e}")
            break
    return out

def main():
    df = pd.read_csv("output/candidatos.csv")
    ape = fetch_apewisdom()
    for col in ["reddit_rank", "reddit_mentions", "reddit_mentions_24h_ago"]:
        df[col] = df["ticker"].map(lambda t: (ape.get(t) or {}).get(col))
    df.to_csv("output/candidatos.csv", index=False)
    hits = df.dropna(subset=["reddit_mentions"]).sort_values("reddit_mentions", ascending=False)
    lines = ["", "## Contexto social — mentions Reddit (ApeWisdom, fora do score)",
             f"*Obtido no momento da execução; {len(hits)} dos {len(df)} candidatos aparecem no top de mentions.*", "",
             "| Ticker | Rank Reddit | Mentions | Mentions há 24h |", "|---|---|---|---|"]
    for _, r in hits.head(15).iterrows():
        lines.append(f"| {r['ticker']} | {int(r['reddit_rank'])} | {int(r['reddit_mentions'])} | "
                     f"{int(r['reddit_mentions_24h_ago']) if pd.notna(r['reddit_mentions_24h_ago']) else '—'} |")
    with open("/dev/null", "a") as f:
        f.write("\n".join(lines) + "\n")
    print(f"OK: {len(hits)} candidatos com dados Reddit; CSV e calendário atualizados.")

if __name__ == "__main__":
    main()
