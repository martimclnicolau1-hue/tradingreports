# O Escolhido — sistema de research de earnings (contexto permanente)

Qualquer agente que abra este repo lê isto primeiro. Este ficheiro dá o
contexto; **não dá licença para improvisar** — na routine diária, o prompt
das 3 fases manda sempre sobre este documento.

## O que é isto
Sistema autónomo de research de earnings dos EUA. Cada dia útil analisa
todas as empresas que reportam (AMC de hoje + BMO de amanhã), escolhe no
máximo **UMA** — "O Escolhido", a de melhor rácio EV/risco — e envia um
email-brief até às ~20:00 Europa/Lisboa com o caso a favor, os
fundamentais explicados, a pesquisa do dia, o caso CONTRA e o plano de
execução. O prazo de decisão é 21:00 (fecho de NY). "NÃO HÁ TRADE HOJE"
é um veredicto válido e obrigatório quando nada passa os limiares.

**O sistema é INFORMATIVO. Nunca produz recomendações de compra/venda
nem tamanhos de posição para além dos parâmetros que o próprio utilizador
fixou em config. As decisões são do utilizador. (Invariante desde a v1.)**

## As leis da casa (inegociáveis — violar isto é corromper o projeto)
1. **Pré-registo**: toda a mudança metodológica é escrita em
   `output/metodologia.md` ANTES de ver resultados, com commit datado a
   provar a ordem. Alterações silenciosas pós-resultados = p-hacking.
2. **Tribunal**: mudanças de modelo (features, painel, regras de score)
   só entram vencendo um tribunal A/B walk-forward com Gates
   pré-registados (não-regressão, edge, calibração). Adoção é mecânica.
3. **Honestidade > conveniência**: contaminações, look-aheads e
   survivorship são CONFESSADOS por escrito nas adendas (há vários
   exemplos: contaminação do braço B v13, holdout queimado, consenso
   vintage). Nunca se esconde uma limitação para o número parecer melhor.
4. **Visibilidade em vez de exclusão silenciosa**: flags forenses
   mostram-se (🚩), estreantes listam-se, excluídos por liquidez
   nomeiam-se. Tudo o que é filtrado é contado.
5. **O veredito é da série, nunca de um evento**: probabilidades
   calibradas de ~30% falham 70% das vezes por contrato. O ledger
   (`data/picks_log.csv`) acumula; o julgamento é ao evento ~20.
6. **criterios_sucesso.md está CONGELADO** (commit 4ee6478) — define a
   validação v15 e não se altera; mudá-lo exige recomeçar a validação.

## Arquitetura e fluxo
- **`run_pipeline.sh`** — entrypoint único da routine. Fases:
  `preparar` (pipeline → brief+escolhido), [pesquisa do agente],
  `enviar` (webhook → pós-processos → commit do estado). Deadline duro
  19:50: aborta e envia alerta de FALHA pelo mesmo webhook.
- **`src/`**: `universe` (calendário Nasdaq) · `fetch` (yfinance com
  caches; preços incrementais) · `metrics`/`rescore_v3` (score legado +
  flags forenses — flags são LIVE-only, nunca backtest) · `factor_study`
  (painel de features point-in-time) · `ev_engine` (kNN analogs) ·
  `gbm_engine` (o motor: GBM + conformal + cabeças calibradas P≥5%/P≥20%
  + tribunais) · `escolhido` (o email: regra ra=EV/largura, gates
  sem-trade, fricção, plano) · `daily_brief` (brief completo de arquivo)
  · `send_webhook` (Make) · `state_bundle` (despensa 57MB p/ cloud) ·
  `finra_short`/`finra_si` (short data PIT) · `emi`, `chain_archive`,
  `hype_calc`, `snapshot_estimates` (contexto + arquivos PIT próprios) ·
  `monitor` (tripwires + regime + liquidação do ledger) ·
  `edgar_universe` (universo canónico 2019-2025 com mortas, v15).
- **`data/`**: caches (gitignored) EXCETO `chains/`, `estimates/`,
  `picks_log.csv`, `state.tar.gz` — esses são estado versionado.
- **Regra de medição/saída (fixa desde v8)**: y = fecho-a-fecho
  (AMC: fecho D → fecho D+1; BMO: fecho D−1 → fecho D). Idêntica em
  backtest e produção. Não se testa outra.
- **Regra do Escolhido (v13.2/v14)**: rank = gbm_ev ÷ (q90−q10);
  elegível = zero flags + ldv≥7,0 (~$10M/dia) + ra≥0,05 + EV≥1%.

## Estado atual (2026-08-06)
- **v14/v15**: FEATS_V14 em produção (fusão de colineares adotada por
  tribunal — evidência de desenvolvimento, confirmação pendente no
  walk-forward v15 e no ledger). Universo sem piso de mcap (decisão do
  utilizador; 1.703 candidatos/semana). Email de Escolhido único ~20:00.
- **Validação v15 em curso**: universo canónico EDGAR (form.idx →
  submissions, mortas incluídas) em crawl; segue-se preços das mortas
  (Stooq/AlphaVantage, matching ≥85%/ano ou parar), painel v15,
  simulador da estratégia com custos, walk-forward trimestral expansivo,
  relatório PASSOU/FALHOU contra criterios_sucesso.md, holdout separado
  (contaminação declarada).
- **Roadmap Fase C**: EX-99.1 → sandbag 2 regimes; Form 4 oportunista;
  Lazy Prices; NLP das calls (quando o painel PIT de consenso maturar).

## Documentos-fonte (por ordem de autoridade)
1. `criterios_sucesso.md` — congelado; a régua da validação
2. `output/metodologia.md` — a lei completa v1→v15, com adendas datadas
3. `docs/plano_validacao_v15.md` + `docs/auditoria_fontes.md`
4. `studies/` — estudos datados (bigwinners, autopsia, retro2026…)

## Segredos e rede
`MAKE_WEBHOOK_URL` vive no environment (nunca no repo). Domínios que o
pipeline toca: Yahoo (query1/query2/fc), api.nasdaq.com, FINRA (api/cdn),
SEC (www/data/efts), tradestie, apewisdom, wikimedia, hook.eu1.make.com.
