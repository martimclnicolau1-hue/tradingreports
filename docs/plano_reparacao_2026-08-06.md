# Plano de reparação — 2026-08-06 (~19:30 UTC)
*Escrito após auditoria da sessão de análise (branch
`claude/analise-problemas-progresso-wl6qc3`). Contexto: o container da
sessão de trabalho anterior morreu levando todo o estado não versionado;
esta auditoria encontrou além disso dois defeitos que tornariam o runner
cloud incapaz de guardar estado mesmo quando corre bem. Reparações aqui
listadas são OPERACIONAIS (custo/fiabilidade, não critério) — zero
mudanças de método, pesos ou limiares; ao implementar, registar NOTA
datada na metodologia por transparência.*

## Diagnóstico (tudo verificado nesta sessão, não especulado)

### D1 — CRÍTICO: o `.gitignore` proíbe a despensa que o pipeline tenta commitar
`data/*` (linha 2) ignora `data/state.tar.gz` e `data/edgar/**`.
Verificado com `git check-ignore -v` e reproduzido em repo de teste:
`git add A B` com B ignorado adiciona A, recusa B com exit 1 — e o
passo 5 do `run_pipeline.sh` esconde esse erro com `2>/dev/null`.
Consequência dupla:
- o commit "estado <data>" nasceria com chains/estimates/picks_log mas
  **sem `data/state.tar.gz`** — parece sucesso, é perda silenciosa;
- o desenho inteiro do estado cloud (metodologia v14§5, "despensa
  commitada a cada corrida") está inoperante: **toda** a corrida cloud
  começa fria (backfill >1h) para sempre.
O CLAUDE.md afirma que `state.tar.gz` é estado versionado — o
`.gitignore` contradiz o contrato documentado.

### D2 — CRÍTICO: falha de envio destrói a noite inteira
`MAKE_WEBHOOK_URL` **não está definido** no environment cloud (a própria
sessão anterior o sabia — o check-in agendado das 20:27 UTC relembra-o).
`send_webhook` sai com exit 3 → `fail "envio webhook"` → o
`run_pipeline.sh` aborta ANTES dos passos 4-5. Perde-se: monitor (o
ledger não liquida — o DCH de hoje liquida amanhã ao fecho), snapshot de
estimativas, rnp_test, e o pack+commit do estado. Um secret em falta ou
um webhook em baixo não devia custar a despensa nem a liquidação do
ledger.

### D3 — Estado da sessão anterior PERDIDO com o container
Não versionados e portanto mortos: caches de preços/fundamentais/info,
`output/factor_panel.csv` (painel de 27.184 eventos), checkpoint do
crawl EDGAR (v15 P2). Era evitável com D1 reparado; agora exige
reconstrução a frio (>1h — o prompt da routine já a prevê no passo 4).

### D4 — Estado operacional real (não é defeito, é o ponto de partida)
- Routine `escolhido-diario` existe (cron `3 16 * * 1-5` UTC = 17:03
  Lisboa; nota no nome sobre a mudança de hora no inverno) e disparou um
  teste às 17:56 UTC em sessão própria; às 18:32 UTC ainda sem push ao
  main (compatível com cold build em curso). Check-in de verificação
  agendado para as 20:27 UTC na sessão anterior.
- Rede DESTE ambiente: SEC OK (form.idx 200, data.sec.gov 200);
  Yahoo devolveu 429 ao curl simples — verificar se o yfinance passa
  (sessão/crumb próprios) na corrida de teste antes de assumir bloqueio.
- Dependências Python não instaladas em container fresco (o prompt da
  routine já manda instalar `requirements-lock.txt`).

### D5 — Menores (baratos, aproveitar a passagem)
- `send_webhook.py`: se `escolhido_<data>.html` existir sem o `.md`,
  `primeira` fica por definir → NameError na linha do `sem_trade`.
- Rodapé do email aponta para `output/brief_<data>.md`, que é
  gitignored (`output/brief_*`) — o leitor nunca o consegue abrir;
  versionar os briefs ou remover a referência.
- ADENDA v14 ("dry-run cloud, custo medido") por preencher.
- Re-tribunal limpo do universo estabilizado: fica para o job mensal
  (dia 1), como pré-registado — NÃO faz parte desta reparação.

## Reparações

### F1 — Código (neste branch; precisa de estar no main antes das 17:03 de amanhã)
1. **`.gitignore`**: acrescentar exceções `!data/state.tar.gz` e
   `!data/edgar/` — a despensa e o checkpoint/universo EDGAR passam a
   sobreviver à morte de containers.
2. **`run_pipeline.sh`**:
   - retirar o `2>/dev/null` do `git add` (falhas de add passam a ser
     visíveis e fatais no log);
   - extrair os passos 4-5 (pós-processos + pack/commit do estado) para
     uma função `preserva_estado` que corre SEMPRE — incluindo no
     caminho de falha do envio (o email pode falhar; o monitor e a
     despensa não podem ir atrás).
3. **`src/edgar_universe.py`**: no checkpoint de cada 500 CIKs, fazer
   também commit+push do checkpoint (agora versionável) — o crawl passa
   a ser retomável entre sessões/containers, não só dentro da mesma.
4. **`src/send_webhook.py`**: inicializar `primeira = ""` antes do
   bloco do subject (D5).
5. **Metodologia**: NOTA datada "reparações operacionais v15.2c"
   (transparência; nada de metodológico muda).
6. Decisão do utilizador em F1: briefs versionados (custo ~centenas de
   KB/dia) ou remover a referência do rodapé — propor a 2ª por defeito.

### F2 — Ação do utilizador (bloqueante para haver email)
Adicionar o secret **`MAKE_WEBHOOK_URL`** ao environment Default do
claude.ai/code. Primeira validação com `DRYRUN=1` (email só ao dono).
Sem isto o sistema fica "preparar-only": escolhido gerado e arquivado,
zero emails — e com F1.2 o estado passa a salvar-se na mesma.

### F3 — Reconstruir a despensa (hoje à noite)
1. Esperar o desfecho do teste da routine (check-in das 20:27 UTC
   verifica). NOTA: mesmo que o teste "passe", o commit de estado dele
   NÃO contém `state.tar.gz` (D1) — não confundir com sucesso.
2. Com F1 no main: numa sessão cloud, `pip install -r
   requirements-lock.txt` → `python3 -m src.backfill` → `python3 -m
   src.factor_study` (cold, >1h, não abortar por demora) → `DRYRUN=1
   bash run_pipeline.sh preparar` → `python3 -m src.state_bundle --pack`
   → commit "estado 2026-08-06" com a despensa DENTRO (verificar com
   `git show --stat`).
3. Preencher a **ADENDA v14** com o custo medido do dry-run.

### F4 — Retomar a validação v15 (P2 → P3)
1. Relançar `python3 -m src.edgar_universe` em sessão dedicada
   (rede SEC verificada OK). Com F1.3, o checkpoint fica commitado a
   cada 500 CIKs — a queda de um container deixa de custar o crawl.
2. No fim: relatório do universo canónico (nº de eventos, AMC/BMO/
   intermédio contado) e cruzamento Alpha Vantage delisted (P2 do plano).
3. Seguir para P3 (preços das mortas; **gate: matching ≥85%/ano ou
   PARAR**) → P4-P7 conforme `docs/plano_validacao_v15.md`. Nada disto
   corre no horário da routine diária (não competir com o deadline).

### F5 — Amanhã (2026-08-07): prova de vida completa
- Routine das 17:03 com despensa quente: verificar commit "estado
  2026-08-07" **com** `state.tar.gz`, e duração <60 min (senão aplica-se
  o pré-registado: cap por liquidez vai a decisão do utilizador).
- Monitor liquida o DCH (evento 1 do ledger) ao fecho — garantido por
  F1.2 mesmo que o webhook ainda falte.
- Se `MAKE_WEBHOOK_URL` já existir: primeiro email real ~20:00.

## Ordem e dependências
F1 (código, ~30 min) → **merge a main** (decisão do utilizador; a
routine clona o main, o branch de trabalho não lhe serve) → F2
(utilizador, 5 min) → F3 (1-2h de máquina, hoje) → F4 (paralelo, sessão
própria) → F5 (verificação amanhã). Sem F1, tudo o resto continua a
escrever em areia.
