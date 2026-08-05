# Event Calendar Pipeline

Pipeline reprodutível de screening de catalisadores (earnings + eventos
binários) para uma janela temporal configurável, com dados gratuitos
(yfinance + SEC EDGAR). Produz um **calendário factual** com estatísticas
e estado de verificação por dado — **não** produz recomendações de
compra/venda nem dimensionamento de posições.

## Uso

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Outputs:
- `output/candidatos.csv` — universo completo com scores e componentes
- `output/calendario.md` — calendário dia-a-dia em pt-PT com flags de verificação
- `data/` — cache (timestamps = quando os dados foram realmente obtidos)

## Antes de correr
1. Edita `src/config.py`: janela, universo, `SEC_USER_AGENT` (põe o teu email — exigência da SEC).
2. `MANUAL_EVENTS` (PDUFAs etc.) não são verificáveis automaticamente — confirma cada um na FDA/IR.

## Estrutura
- `src/config.py` — janela, universo, parâmetros (edita aqui)
- `src/fetch.py` — dados com cache + flag `verified` por fonte
- `src/metrics.py` — reações históricas, edge ratio, técnica, forense, score pré-registado
- `src/simulate.py` — Monte Carlo educativo + sanity-backtest walk-forward
- `src/report.py` — CSV + calendário markdown
- `output/metodologia.md` — metodologia pré-registada (lê antes de correr)

## Avisos
- yfinance é scraping não-oficial: pode partir ou devolver dados incompletos; o
  pipeline degrada para "—" (nunca estima).
- Amostras de n≈12 prints por ticker têm ICs largos; o relatório imprime-os.
- Isto é ferramenta de investigação/educação. Não é aconselhamento financeiro.

## Modo diário (v6)
- Tarefa agendada "brief-earnings-diario": dom–qui às 21:45 de Lisboa (com o
  **Mac ligado e a app Claude aberta** — se estiver fechada, corre no próximo arranque).
- Fluxo: `EVENTCAL_ROLLING=1 python run.py` (janela = hoje→+7d, opções só top-100)
  → rescore → ev_engine → gbm_engine → hype_calc → `python -m src.daily_brief` → email via Make para luis@nikufra.ai.
- O brief cobre AMC de amanhã + BMO de depois de amanhã (prazo único: amanhã 21:00).
- Graus A/B/C = qualidade de setup (regra na metodologia v6), nunca recomendações.
- **Dependência**: a ligação Gmail no Make tem de estar autenticada (Make.com →
  Connections → google-email → Reauthorize se aparecer 401). Falhas ficam em
  output/brief_errors.log e o brief fica sempre disponível localmente.
