# -*- coding: utf-8 -*-
"""v14: despensa portátil do runner cloud — data/state.tar.gz.

--pack: empacota o estado essencial (preços TRIMADOS a 3 anos — chegam para
todas as features point-in-time: 252 barras + folga; earnings/info/fin/
optclean/vix/FINRA). Rebuilds profundos de painel (10 anos) são trabalho do
job mensal, não do noturno (metodologia v14§5).
--unpack: se data/ vier vazio (clone fresco na cloud), extrai o bundle.

Uso: python3 -m src.state_bundle --pack | --unpack
"""
import glob
import io
import os
import sys
import tarfile

import pandas as pd

BUNDLE = "data/state.tar.gz"
TRIM_BARS = 800  # ~3,2 anos de barras: 252 (52w) + 65 (relvol) + folga larga


def pack():
    n_prices = n_other = 0
    with tarfile.open(BUNDLE, "w:gz") as tar:
        for p in glob.glob("data/prices_*.csv"):
            try:
                df = pd.read_csv(p, index_col=0)
                trimmed = df.tail(TRIM_BARS).to_csv().encode()
                info = tarfile.TarInfo(p)
                info.size = len(trimmed)
                tar.addfile(info, io.BytesIO(trimmed))
                n_prices += 1
            except Exception:
                continue
        for pat in ["data/earnings_*.json", "data/info_*.json", "data/fin_*.pkl",
                    "data/optclean.json", "data/vix.csv", "data/finra/short_daily.csv.gz",
                    "data/finra/done.txt", "data/wsb_top.json"]:
            for p in glob.glob(pat):
                tar.add(p)
                n_other += 1
    mb = os.path.getsize(BUNDLE) / 1e6
    print(f"state.tar.gz: {n_prices} preços (trim {TRIM_BARS} barras) + {n_other} outros = {mb:.0f} MB")
    if mb > 95:
        print("[AVISO] bundle >95MB — perto do limite de ficheiro do GitHub (100MB); "
              "reduzir TRIM_BARS ou mover para artifact/release")


def unpack():
    if len(glob.glob("data/prices_*.csv")) > 100:
        print("despensa já cheia — sem unpack")
        return
    if not os.path.exists(BUNDLE):
        print("[AVISO] sem bundle e sem caches — a corrida vai fazer fetch frio (LENTA)")
        return
    with tarfile.open(BUNDLE, "r:gz") as tar:
        tar.extractall(".")
    print(f"despensa extraída: {len(glob.glob('data/prices_*.csv'))} preços")


if __name__ == "__main__":
    if "--pack" in sys.argv:
        pack()
    elif "--unpack" in sys.argv:
        unpack()
    else:
        print("usa --pack ou --unpack")
