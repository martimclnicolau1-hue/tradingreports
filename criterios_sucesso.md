# Critérios de sucesso — validação da estratégia "O Escolhido"
*Congelado ANTES de qualquer corrida de validação (regra 8 do spec).
Este ficheiro não se altera depois do primeiro fold correr; qualquer
proposta de mudança exige nova validação do zero.*

## O que está a ser validado
A ESTRATÉGIA completa, não o classificador: por dia de teste, aplicar a
regra integral de decisão e medir o P&L líquido da carteira de 1 posição.

## Regra de decisão (fixa)
- Universo do dia (ex-ante, canónico EDGAR): US, 8-K item 2.02, AMC-hoje
  + BMO-amanhã (decisão do utilizador 2026-08-06)
- Elegibilidade PIT às 17:03 Lisboa: log_dollar_vol ≥ 7,0 (~$10M/dia),
  preço ≥ $1, ≥4 eventos prévios, ≥260 barras de preços
- Pick: máx. 1/dia, topo de ra = gbm_ev ÷ (q90−q10), exigindo ra ≥ 0,05
  E gbm_ev ≥ +1,0%; senão "NÃO HÁ TRADE HOJE" (veredicto válido)
- Flags forenses: NÃO entram no backtest (não-PIT); ficam no live
  (divergência declarada — decisão do utilizador 2026-08-06)

## Regra de saída (fixa desde v8, reactions.py)
Fecho-a-fecho: AMC = fecho D → fecho D+1; BMO = fecho D−1 → fecho D.
Idêntica em backtest e produção. Proibido testar alternativas.

## Modelo de custos (fixo; subtraído a TODOS os números reportados)
- Half-spread por lado, por tier de liquidez: ldv ≥ 8,0 → 5 bps/lado;
  7,0 ≤ ldv < 8,0 → 20 bps/lado
- Impacto: +5 bps por lado adicional
- Total round-trip: tier alto 20 bps; tier baixo 50 bps
- Nenhum número bruto sem o líquido ao lado

## Critérios de PASSAGEM (walk-forward E holdout, ambos)
1. Spearman(score, retorno realizado) out-of-sample > 0,05
2. Retorno médio LÍQUIDO por evento do Escolhido > 0, com erro-padrão
   e n reportados (significância: média − 2·SE > seria ideal; mínimo
   exigido: média > 0 e média − 1·SE > 0)
3. MEDIANA líquida do Escolhido > 0 (não se vive só de cauda direita)
4. Calibração: declive da regressão retorno~EV_previsto ∈ [0,5; 1,5]
5. Reportar sempre: win-rate, drawdown máximo, nº de dias sem trade
PASSA = todos os critérios no walk-forward E no holdout. Caso contrário
FALHA, e o relatório di-lo sem maquilhagem.

## Confissões pré-registadas (limitam o que o veredicto pode afirmar)
- HOLDOUT (Q2-Q3 2026): foi visto pelos tribunais v10-v14 durante o
  desenvolvimento. Avalia-se UMA vez, mas o veredicto carrega esta
  contaminação declarada; o holdout virgem real é o ledger live
  (picks_log.csv, evento 1 = 2026-08-06).
- Consenso histórico (yfinance) é vintage única não reconstruível às
  17:03 de cada dia; as features usam apenas factos de trimestres
  FECHADOS (surpresas realizadas), nunca o consenso corrente.
- Sandbag 2-regimes (guide-down vs pessimismo de analistas) entra na
  validação v2 via EX-99.1 do EDGAR; a v1 usa o sandbag atual com esta
  limitação declarada.
- Eventos de mortas sem preço recuperável: imputação de pior decil SÓ
  para falência/compliance (M&A nunca é imputada — decisão do
  utilizador); veredicto reportado como intervalo.

## Reprodutibilidade (regra 9)
Seed 42 em tudo; manifesto de dados (SHA-256 + datas) por corrida;
log por fold committed; qualquer número do relatório re-derivável.
