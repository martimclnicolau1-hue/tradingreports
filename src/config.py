# -*- coding: utf-8 -*-
"""Configuração central do pipeline.

Edita AQUI a janela temporal e o universo de tickers antes de correr.
Tudo o resto é derivado. Nenhum número de mercado está hardcoded no
código — os dados vêm todos das fontes ao vivo quando corres o run.py.
"""
import os
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Janela do evento (inclusiva). Ajusta a cada scan.
# ---------------------------------------------------------------------------
if os.environ.get("EVENTCAL_ROLLING") == "1":
    WINDOW_START = date.today()
    WINDOW_END = date.today() + timedelta(days=7)
else:
    WINDOW_START = date(2026, 8, 5)
    WINDOW_END = date(2026, 8, 15)

# ---------------------------------------------------------------------------
# Universo candidato. O pipeline valida a data de earnings de cada ticker
# via yfinance e DESCARTA (com aviso) os que não tiverem evento confirmado
# dentro da janela. Acrescenta livremente — o custo é só tempo de download.
# ---------------------------------------------------------------------------
AUTO_UNIVERSE = True          # v5: descobrir universo via calendário de mercado
ENRICH_TOP_N = 100            # v6: opções só para o top-N do pré-score (custo, não critério)
RECALL_MIN_UNIVERSE = 50      # v11: gate de recall (warn-only) — universo abaixo disto = suspeita
RADAR_MIN_LOG_DVOL = 7.0      # v11: piso de liquidez do Radar (≈$10M/dia) — execução, não alfa
ALWAYS_ENRICH = ["LLY", "SE", "DLO", "ONON", "INOD", "CELH", "APP", "ROKU"]
MIN_MCAP = 0                  # v13: piso REMOVIDO por decisão do utilizador (v5§2 nunca teve
                              # evidência; CLRO-class entra e fica visível como Estreante)
SCOPE_DAYS = 3                # v13: âmbito unificado (enriquecimento/chains/hype) — antes divergia T+2 vs T+3

# Fallback manual (usado só se todas as fontes de calendário falharem)
UNIVERSE_FALLBACK = [
    # nomes do scan do utilizador
    "AXON", "APP", "BROS", "FROG", "NVAX", "CLSK", "SMCI", "SE", "CRWV",
    "CAVA", "ONON", "ASTS", "COHR", "NBIS", "CSCO", "AMAT", "JD", "DLO",
    "STNE", "LNTH", "MRNA", "LITE",
    # ad-tech / software peers (read-through APP, FROG)
    "TTD", "DDOG", "NET", "MDB", "TEAM", "GTLB", "PATH", "U", "RBLX",
    # semis / ótica / hardware peers (read-through COHR, SMCI)
    "NVDA", "AVGO", "MRVL", "ANET", "DELL", "VRT", "SITM", "AAOI", "IIVI",
    # consumo / restauração peers (read-through BROS, CAVA)
    "SBUX", "CMG", "WING", "SG", "DPZ", "SHAK",
    # biotech / farma com catalisadores frequentes
    "BNTX", "SRPT", "IONQ", "VKTX", "ALNY", "RARE", "IMVT",
    # cripto-adjacentes (read-through CLSK)
    "MARA", "RIOT", "COIN", "HUT", "WULF", "IREN",
    # espaço / defesa (read-through ASTS, AXON)
    "RKLB", "LUNR", "PL", "KTOS", "AVAV",
    # outros high-beta habituais de agosto
    "HIMS", "FUBO", "GDRX", "INOD", "MNDY", "OKLO", "AFRM", "TOST",
    "DUOL", "IOT", "TWLO", "SHOP", "LYFT", "PTON", "SOFI", "PLTR",
    # expansão ronda 2 (2026-08-04): mega-caps e nomes líquidos da semana
    "AMD", "DIS", "UBER", "ABNB", "DASH", "SNAP", "PINS", "RDDT", "HOOD",
    "CVNA", "MELI", "LLY", "NVO", "ANET", "FTNT", "EXPE", "ARM", "TTWO",
    "EA", "ZG", "W", "ETSY", "TPR", "RL", "DE", "BABA", "BIDU", "NTES",
    "TME", "SONY", "AKAM", "GDDY", "BILL", "MNST", "SWKS", "MTCH",
    "YELP", "TDOC", "OSCR", "CELH",
]

# Posição existente do utilizador — usada apenas para a sinalizar no output,
# nunca para gerar recomendações de compra/venda.
EXISTING_POSITIONS = {
    "LLY": "posição de €1.000 declarada pelo utilizador a 2026-08-04",
    "AXON": "posição antiga declarada — estado atual por confirmar pelo utilizador",
    "GCT": "posição de €1.000 declarada pelo utilizador a 2026-08-05 (report 06/08 BMO)",
}

# ---------------------------------------------------------------------------
# Macro overlay — datas de releases oficiais (BLS/Census). Confirma no site
# oficial antes de confiar: https://www.bls.gov/schedule/news_release/
# ---------------------------------------------------------------------------
MACRO_EVENTS = [
    {"date": date(2026, 8, 7), "name": "Nonfarm Payrolls (Jul)", "time_et": "08:30", "source": "BLS"},
    {"date": date(2026, 8, 12), "name": "CPI (Jul)", "time_et": "08:30", "source": "BLS"},
    {"date": date(2026, 8, 13), "name": "PPI (Jul)", "time_et": "08:30", "source": "BLS"},
    {"date": date(2026, 8, 14), "name": "Retail Sales (Jul)", "time_et": "08:30", "source": "Census"},
]

# Eventos binários não-earnings conhecidos (FDA etc.). O pipeline NÃO tem
# fonte automática fiável e gratuita para PDUFAs — mantém esta lista à mão
# e confirma cada entrada no site da FDA / IR da empresa.
MANUAL_EVENTS = [
    {"ticker": "MRNA", "date": date(2026, 8, 5), "name": "PDUFA mRNA-1010 (gripe)", "verified": False},
    {"ticker": "LNTH", "date": date(2026, 8, 13), "name": "PDUFA MK-6240 (PET tau)", "verified": False},
]

# ---------------------------------------------------------------------------
# Parâmetros quantitativos
# ---------------------------------------------------------------------------
N_PAST_EARNINGS = 12          # nº de reações históricas a analisar
BIG_MOVE_THRESHOLD = 0.10     # |move| >= 10% conta como "movimento grande"
BIG_UP20 = 0.20               # v10: limiar "moonshot" (fixo na metodologia v10)
CACHE_DIR = "data"            # cache local para não martelar as APIs
REQUEST_SLEEP = 0.6           # segundos entre pedidos (rate-limit friendly)
SEC_USER_AGENT = "EventCalendarResearch/1.0 (contacto: luis@nikufra.ai)"
