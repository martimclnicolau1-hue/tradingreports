# Plano de validação v15 — a ESTRATÉGIA, não o classificador
*Escrito APÓS o congelamento de criterios_sucesso.md (commit 4ee6478) —
ordem exigida pela regra 8. Correções do utilizador de 2026-08-06
integradas. O código muda onde conflitue com isto.*

## Estado de partida declarado
- Fusão de colineares ADOTADA (FEATS_V14; Gates 1∧2∧3 — Gate 2 PASSA:
  captura>baseline ∧ Wilson>base). Evidência de DESENVOLVIMENTO (painel
  visto); confirmação pendente no walk-forward v15 + ledger.
- Saída fixa (fecho-a-fecho, v8). Flags forenses: live sim, backtest não.
- Universo estratégico: AMC-hoje + BMO-amanhã.
- Holdout Q2-Q3 2026: contaminado por desenvolvimento — declarado; o
  virgem real é o ledger live.

## P1 — Auditoria de fontes → docs/auditoria_fontes.md (committed)

## P2 — Universo canónico EDGAR (src/edgar_universe.py)
**SEED (correção 1 do utilizador): os CIKs vêm dos form.idx TRIMESTRAIS
2019-2025** (28 ficheiros full-index — TODOS os 8-K históricos, incluindo
mortas), NUNCA do company_tickers.json (mapa atual = survivorship de CIK;
serve apenas para enriquecer os vivos com ticker atual).
Fluxo: form.idx → conjunto de CIKs com 8-K no período → submissions.json
(+ páginas) por CIK → filtrar items contendo "2.02" → acceptanceDateTime
em ET (≥16:00 = AMC do dia; <09:30 = BMO; resto = flag "horário
intermédio", excluído do universo estratégico com contagem reportada).
Rate: ≤8 req/s, User-Agent config.SEC_USER_AGENT, backoff 403/429 com
pausa 10 min, checkpoints/500 CIKs, resumável.
Cruzamento: Alpha Vantage LISTING_STATUS&state=delisted (1 request) →
relatório do nº EXATO de eventos 2019-2025 fora do painel atual.

## P3 — Mortas: classe de morte + preços + matching
**CLASSE DE MORTE (correção 2): no mesmo crawl, classificar cada
deslistada** por M&A / falência / compliance usando os próprios filings
(DEFM14A, SC 14D9 → M&A; 8-K item 1.03 → falência; Form 25/15 sem
aquisição → compliance/voluntário). IMPUTAÇÃO DE PIOR DECIL SÓ para
falência/compliance sem preço recuperável; **M&A NUNCA é imputada**.
Relatório: eventos recuperados por classe e por ano.
**MATCHING (correção 3): cadeia explícita CIK → ticker histórico
(cover page do 8-K + former names do submissions) → símbolo Stooq**
(match direto; fuzzy contra o CSV de deslistadas da AV como 2ª chave).
Taxa de match reportada POR ANO; **abaixo de 85% em qualquer ano →
PARAR e reportar antes de continuar** (sem remendos silenciosos).
Preços: Stooq bulk primeiro; buracos via AV daily (25/dia, priorizado
por nº de eventos); ajustes de splits validados contra 2 fontes nos
overlaps (divergência >2% → excluir com log).

## P4 — Painel v15
Rebuild sobre o universo canónico; features PIT existentes
(factor_study), FEATS_V14, sem flags, |y|≤2,0+guarda. Manifesto de dados
(SHA-256 + datas) por corrida.

## P5 — Simulador da estratégia (src/strategy_sim.py)
Por dia: universo ex-ante canónico → elegibilidade PIT (criterios) →
modelo treinado só no passado → regra completa (ra≥0,05 ∧ EV≥1% → 1
pick; senão SEM TRADE) → P&L líquido (custos de criterios) → curva de
capital, win-rate, MEDIANA, drawdown, dias sem trade; atribuição
substituição-mediana por fold (estabilidade reportada).

## P6 — Walk-forward trimestral expansivo
Q1..QN → QN+1, ~24 folds 2019-2025, nunca reafinar para trás; log por
fold committed; holdout Q2-Q3 2026 avaliado UMA vez, relatório separado,
com a contaminação escrita.

## P7 — Relatórios
docs/validacao_v15.md (folds, curva líquida, calibração, estabilidade,
n/SE, PASSOU/FALHOU vs criterios) → depois docs/holdout_final.md.

## P8 (paralelo) — EX-99.1 no mesmo crawl → sandbag 2 regimes (validação v2)

## Ordem: P1 → P2 (crawl ~60-100 min, background) → P3 (Stooq já; AV
drip diário) → P4 → P5 → P6 → P7; P8 acumula desde P2.
