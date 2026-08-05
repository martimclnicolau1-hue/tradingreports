# Metodologia — pré-registada ANTES de qualquer dado ser descarregado

*Escrita a 2026-08-04, antes da primeira execução do pipeline. Se alterares
pesos ou fórmulas depois de veres resultados, regista aqui a alteração e o
motivo — alterações silenciosas pós-resultados são p-hacking.*

## REVISÃO v2 — 2026-08-04, registada ANTES da primeira execução com dados

A v1 nunca chegou a correr com dados; esta revisão é motivada por (a) pedido
do utilizador (mais sensibilidade fundamental; horizonte 1–2 dias) e
(b) pesquisa de literatura feita a 2026-08-04:

1. **Fundamental 60% → 65%**, com novo bloco de *expectativas/surpresas*
   (o fator fundamental mais relevante a 1–2 dias segundo a literatura
   SUE/"double surprise"): beat rate dos últimos ~8 trimestres, momentum
   de surpresa (últimas 4 vs 4 anteriores) e penalização "beat-and-fell"
   (bater e cair = expectativas demasiado altas — sinal negativo).
2. **Drift D+3 de-weighted (20%→15% da quant)**: PEAD multi-dia está
   documentado como inexistente para não-microcaps desde ~2006 — mantê-lo
   com peso alto seria fingir que uma anomalia arbitrada ainda paga.
3. **Edge ratio sobe (45%→50% da quant)**: as opções sobreavaliam
   sistematicamente o movimento de earnings (volatility risk premium),
   logo edge>1 é raro e genuinamente informativo.
4. **Sentimento social (StockTwits/Reddit) e trades do Congresso = CONTEXTO,
   não score.** Sem evidência de poder preditivo fiável a 1–2 dias; entram
   como colunas + flag de *crowding* (bullish%≥70 e short%float≥15 →
   setup sobrelotado). Adicioná-los ao score sem backtest seria p-hacking.
5. **Aceleração de receita** (2ª derivada, trimestral YoY) entra no bloco
   de crescimento quando os dados trimestrais chegam para a calcular.

### Pesos v2 (fixos a partir daqui)
- **Fundamental 65%**: expectativas/surpresas 30% · crescimento+aceleração+margem 25% ·
  qualidade dos lucros (accruals, FCF/NI, SBC) 25% · sobrevivência+valuation (Altman, net cash, EV/S vs g) 20%
- **Quant 35%**: edge ratio 50% · skew 35% · drift D+3 15%

---

## v1 (histórico — substituída pela v2 antes de qualquer execução)

## Score composto: 60% fundamental / 40% quant (fixo)

### Camada fundamental (60 pontos)
| Componente | Peso | Fonte | Normalização |
|---|---|---|---|
| Crescimento de receita | 22% | yfinance `revenueGrowth` | 0% → 0; ≥50% → 1 |
| Margem bruta | 14% | `grossMargins` | 20% → 0; ≥80% → 1 |
| Conversão FCF/NI | 14% | cashflow stmt | 0 → 0; ≥1,5 → 1 |
| Altman Z'' | 16% | balanço | 0 → 0; ≥6 → 1 |
| Accruals (Sloan) | 14% | invertido | ≥15% do ativo → 0 |
| SBC % receita | 8% | invertido | ≥25% → 0 |
| EV/S ajustado ao crescimento | 12% | EV/S por ponto de crescimento | ≥0,6 → 0 |

### Camada quant (40 pontos)
| Componente | Peso | Definição |
|---|---|---|
| Edge ratio | 45% | mov. histórico médio ÷ mov. implícito; 0,6 → 0; ≥1,5 → 1 |
| Skew direcional | 35% | %(≥+10%) − %(≤−10%) nos últimos 12 prints |
| Drift D+3 pós-subida | 20% | retorno médio D+1→D+3 quando D1 > 0 |

### Regras de honestidade (fixas)
1. Campo em falta = 0,5 (neutro) e conta para `pct_missing`; um candidato com
   >40% de dados em falta não pode ser citado como "top pick" seja qual for o score.
2. Hit rates reportados SEMPRE com IC binomial de Wilson a 95% (n≈12).
3. Haircut de comparações múltiplas: num scan de T tickers, diferenças de
   médias só são citadas como "edge" se excederem 2 erros-padrão (ver
   `simulate.walk_forward_check`). Caso contrário: "indistinguível de ruído".
4. Red flag forense (Altman < 1,1 ou accruals > 10% ou SBC > 20%) é
   reportada SEMPRE ao lado do score, por muito bom que o quant seja —
   fundamentais mandam.
5. Expiração de opções >10 dias após o evento → flag "implícito inflacionado".
6. Nenhum campo é estimado à mão. Fonte falhou → `None` → "—" no relatório.

### O que este pipeline NÃO produz (por decisão, não por limitação)
- Recomendações de compra/venda ou de gestão de posições existentes.
- Tamanhos de posição para o bankroll de um utilizador específico.
- Probabilidades de cenário "inventadas" (o Monte Carlo aceita as TUAS).

### Limitações de dados conhecidas à partida
- Revisões de estimativas 30/90 dias: não disponíveis em fonte gratuita fiável → fora do score.
- Beneish M-Score completo: exige 2 anos de detalhe que o yfinance nem sempre dá → só componentes disponíveis.
- Piotroski F: idem — implementado parcialmente via componentes (accruals, margem, alavancagem).
- 13F: desfasamento de 45+ dias torna-o inútil para uma janela de 15 dias → excluído.
- PDUFA/FDA: sem API gratuita fiável → lista manual em `config.MANUAL_EVENTS`, marcada não-verificada.

---

## REVISÃO v3 — 2026-08-04, após estudo de fatores (output/factor_panel.csv)

Regra registada ANTES do estudo: pesos direcionais ∝ |t| no painel point-in-time;
snapshot fundamental = veto, não peso; ranking conservador para posição única.

Resultados (n=333 eventos, 49 tickers): dist_52w_high t=+2,54 (único ≥2, marginal
após haircut de 5 testes); rsi14 t=+1,72; mom60 t=+1,26; prior_skew t=+0,72;
prior_beat_rate t=-0,13 (zero). Surpresa real t=+4,57 (mecanismo, não negociável).

### Score v3 (aplicação mecânica da regra)
- **Direcional (50%)**, pesos ∝|t| normalizados: dist_52w_high 40% · rsi14 27% ·
  mom60 20% · skew 11% · beat_rate 2%
- **Preço do bilhete (50%)**: edge ratio (implícito vs histórico) — split 50/50
  declarado como prior não testável (sem histórico de implícitos gratuito)
- **Vetos rígidos (posição única, sem diversificação)**: Altman<1,1 OU
  accruals>10% OU SBC>20% da receita OU beat_and_fell>50% → inelegível para
  topo do dia, seja qual for o score
- Honestidade: o único fator com t≥2 é marginal após comparações múltiplas;
  o v3 é "menos mal calibrado" que o v2, não é um sistema com edge provado.

---

## REVISÃO v4 — 2026-08-04, estudo de algoritmos (src/algo_study.py, src/options_clean.py)

Testados empiricamente (567 eventos OHLC / 413 com surpresas):
1. Continuação intradiária pós-gap: gap>5% → open→close +0,42% (t=0,69);
   condicionado a blowout>15%: +1,12%, 57% positivo (t=1,47). Não significativo.
2. Sandbagging (autocorrelação de surpresas): prior_mean_surprise→surpresa
   seguinte t=+4,53; P(blowout) 63% no top-half vs 34-42% no bottom. MAS
   →reação de preço só t=+1,37: maioritariamente já preçado. Entra no
   direcional v4 com peso ∝|t| (18%).
3. Extração limpa da variância do evento (term-structure IV, 2 expirações):
   implementada; expôs divergências até 4× entre estimadores (ex.: AXON edge
   0,61 straddle vs 1,78 clean) → quotes gratuitas de opções são demasiado
   ruidosas fora de horas; edges só citáveis quando ambos os estimadores
   concordam (<1,5× de rácio entre eles).
4. Skew IV put-call 5% OTM + rácio put/call volume: colunas de CONTEXTO
   (literatura Xing/Zhang/Zhao); sem peso sem backtest próprio.
5. ML tabular: rejeitado por aritmética de amostra (deteção de r=0,1 a 80%
   de poder exige n≈780; temos 333).

Pesos v4: direcional 50% (d52 33% · rsi 22% · sandbag 18% · mom60 16% ·
skew 9% · beat 2%) + bilhete 50% (edge_clean quando disponível, senão
straddle). Vetos v3 mantidos.

---

## REVISÃO v5 — 2026-08-04, registada ANTES da primeira execução com universo automático

Motivação: a lista manual de ~120 tickers via ~120 de ~1.000 reportadores da semana
(a ronda 2 manual encontrou a LLY por sorte dirigida). O universo passa a ser
descoberto automaticamente. REGRAS FIXADAS AGORA:

1. **Fontes de calendário**: Nasdaq (api.nasdaq.com/api/calendar/earnings, pública,
   primária — dá data, timing BMO/AMC e market cap); API Ninjas e EarningsAPI
   opcionais atrás de env keys. yfinance = segunda fonte de validação (regra das
   2 fontes mantém-se: date_verified só com yfinance a confirmar ±1 dia; nomes de
   fonte única mantêm-se com flag visível).
2. **Filtros de elegibilidade** (fixos antes de ver resultados): market cap
   ≥ $500M (do próprio feed Nasdaq); os restantes filtros de qualidade acontecem
   downstream como sempre (sem opções → sem edge; forense → vetos).
3. **Gate de aceitação**: recall ≥95% da lista manual atual na janela — se nomes
   conhecidos desaparecerem, é bug de filtro, não descoberta.
4. Scores, pesos e vetos: INALTERADOS (v4). O v5 muda cobertura, não critério —
   deliberadamente, para não misturar duas mudanças numa só versão.
5. Fallback declarado: todas as fontes mortas → lista manual, com aviso no
   calendário. Nunca silencioso.

---

## REVISÃO v6 — 2026-08-04, registada ANTES da primeira execução do modo diário

1. **Top-N de enriquecimento (custo, não critério)**: cadeias de opções só para o
   top ENRICH_TOP_N=100 do pré-score ∪ ALWAYS_ENRICH (nomes com estudo profundo)
   ∪ posições declaradas. Fora do top-N: edge "não avaliado" (—), nunca inventado.
2. **Graus do brief diário (regra fixa)**: A = sem vetos + data verificada + dois
   estimadores concordam (<1,5×) + edge conservador ≥1,0 + beat&fell <50%;
   B = sem vetos + data verificada mas estimador único ou edge 0,8–1,0;
   C = restantes não-vetados (vigia). Vetados listados com motivo.
3. **Âmbito temporal do brief das 21:45 de T**: AMC de T+1 + BMO de T+2 (ambos com
   prazo T+1 21:00 — ≥19h de antecedência). BMO de T+1 aparece só como informação.
4. O brief é informativo: graus de confiança e prazos, sem diretivas. Rodapé de
   honestidade obrigatório em todos os envios.

---

## REVISÃO v7 — 2026-08-05, registada ANTES da primeira execução do ev_engine

Requisito do utilizador: ranking por VALOR ESPERADO (80%×+20% > 100%×+1%) + fator
de hype/atenção. REGRAS FIXADAS AGORA:

1. **EV por analogs (kNN)**: painel expandido a todos os tickers em cache
   (novas colunas: event_date, sandbag point-in-time, log_mcap, rel_volume
   pré-evento). Matching: 8 features (dist_52w_high, rsi14, mom60,
   prior_avg_move, prior_up_big_rate, sandbag, log_mcap, rel_volume),
   z-scores clipados ±3, distância euclidiana MASCARADA (dims mutuamente
   presentes; <4 partilhadas → ∞). Candidato precisa ≥6/8 features e ≥30
   vizinhos finitos, senão "EV não avaliado" — NUNCA imputação neutra.
   k=50; EV=média(y); decomposição p_up/e_up/p_big/tail_up/downside/p5;
   IC bootstrap 200×, seed 42. EV é ORDENAÇÃO, não previsão de lucro.
2. **Vetos forenses sobrepõem-se ao EV** — vetado nunca entra no ranking EV.
3. **Pesos v4 congelados** — o painel expandido serve só para matching; re-pesar
   com ele seria post-hoc. |y|>1,0 descartado como erro de dados (contado).
   log_mcap tem look-ahead declarado (mcap atual em eventos históricos).
4. **Validação walk-forward pré-registada**: cronológica por event_date, EV de
   cada evento calculado só com eventos estritamente anteriores (≥300);
   quintis de EV; gate: spread topo-fundo com teste 2-SE + Spearman t.
   Sem spread → brief rotula "ordenação heurística, edge não provado".
   Spread NEGATIVO significativo → secção EV não publica. Adenda datada abaixo
   após correr.
5. **Hype em duas camadas**: (a) rel_volume pré-evento = proxy backtestável de
   atenção (Barber-Odean/Da-Engelberg-Gao) → 8ª feature do kNN, validada pelo
   mesmo gate; (b) hype_score social ao vivo 0-100 (Reddit mentions+delta, WSB,
   Wikipedia pageviews 7d/30d, volume de opções, rel_volume atual; pesos iguais
   por falta de dados para otimizar — declarado) → CONTEXTO/badge, SEM peso no
   EV (sem histórico social → sem backtest → sem peso). Caveat fixo no brief:
   picos de atenção sobem no curto prazo e revertem depois.
6. tail_ratio (P95 das subidas próprias ÷ implícito; ≥6 subidas senão NaN) e
   call_cheapness (iv_skew) = CONTEXTO, zero peso.

### ADENDA v7 — resultados da validação walk-forward (2026-08-05)
n=5.934 eventos avaliados cronologicamente. Quintis de EV (crescente):
+0,05% / +0,36% / +0,01% / +0,58% / +0,83%. Spread topo-fundo = +0,78pp;
NÃO passa o teste 2-SE; Spearman t=0,9. VEREDITO (aplicação da regra
pré-registada): o ranking EV publica-se rotulado "ordenação heurística,
edge não provado". Direção dos quintis é consistente com utilidade de
ordenação; significância estatística não existe — e o brief di-lo em cada envio.
Self-test sintético: PASSOU (spread 0,199, >2SE — o motor deteta sinal quando existe).

---

## REVISÃO v8 — 2026-08-05, registada ANTES do primeiro fit

Objetivo central (utilizador): máxima precisão do TOPO do ranking + confiança
calibrada por pick + abstenção. REGRAS FIXADAS AGORA, antes de qualquer treino:

1. **Motor GBM**: HistGradientBoostingRegressor, quantile loss (Q10/Q50/Q90) +
   regressor de média. Hiperparâmetros CONGELADOS: max_iter=300, lr=0.05,
   max_depth=4, l2=1.0. Sem tuning fora de folds de treino (tuning global = leak).
2. **Features**: as 8 do kNN + VIX no dia do evento (^VIX, point-in-time
   verdadeiro), dia-da-semana, timing AMC/BMO. Sector fica FORA nesta versão
   (one-hot com look-ahead adiado).
3. **Intervalos**: CQR — calibração conformal split nos últimos 20% cronológicos;
   cobertura alvo 80%, verificada e publicada.
4. **Tribunal kNN v7 vs GBM v8**: mesmo harness walk-forward ancorado, 30 folds
   cronológicos. MÉTRICA PRIMÁRIA: retorno médio realizado do TOP-1 e TOP-3 por
   fold (precisão do topo). Secundárias: spread quintil 2-SE, Spearman t,
   cobertura, curva de calibração P(≥+10%). Publica-se o motor com melhor TOP-3
   realizado; sem 2-SE no spread → rótulo "heurística" mantém-se.
5. **Meta-modelo de confiança (meta-labeling)**: classificador sobre os picks
   top-3 históricos do primário; target = subiu ≥+5%; calibração isotónica
   dentro de folds. **Limiar de abstenção: P_calibrada ≥ 0,65.** O brief abre
   com o pick + P calibrada + frase de auditoria (previsto vs realizado do
   bucket correspondente), OU "SEM SINAL DE ALTA CONFIANÇA HOJE".
6. **Shrinkage empírico-Bayes**: beat_rate e sandbag por ticker encolhidos para
   a média global com peso n/(n+8) (prior fixo n0=8, declarado).
7. Limpeza de código: estudos one-off arquivados em studies/ (auditabilidade);
   fontes mortas removidas; computação de reações consolidada em reactions.py
   (fórmula única, paridade painel/candidatos garantida por construção).
8. Research web automático dos top-3 no brief diário: máx 3 nomes, fontes
   citadas, itens não confirmados marcados, zero linguagem de diretiva.

### ADENDA v8 — resultados do tribunal e calibração (2026-08-05)
30 folds ancorados, 5.434 eventos avaliados:
- **Vencedor TOP-3 (regra pré-registada): GBM** — TOP-3 realizado +3,20%/fold
  (±2,15) vs kNN +1,83% (±2,09). TOP-1: kNN +6,89% (±4,75 — ruidoso) vs GBM
  +3,13% (±3,71). Nenhum spread quintil passa 2-SE → rótulo "heurística" mantém-se.
- **Cobertura conformal: 0,799 vs alvo 0,80 — a garantia matemática cumpriu-se.**
- **Calibração isotónica excelente onde há dados**: previsto 24%→realizado 23%;
  33%→32%; 43%→42%. As probabilidades anunciadas SÃO honestas.
- **DESCOBERTA CENTRAL: em 5.429 eventos históricos, o modelo calibrado NUNCA
  atingiu P(≥+5%) ≥ 0,65** (máximo observado ~0,60, n=1). O limiar de abstenção
  pré-registado está acima do alcançável → o sistema abster-se-á por defeito e
  mostrará o melhor pick com a sua probabilidade verdadeira (~30-50%).
  INTERPRETAÇÃO HONESTA: o mercado não oferece eventos de earnings em que um
  modelo calibrado com dados públicos chegue a 65% de confiança numa subida de
  +5%. A "certeza" máxima honesta que existe é ~40-60%, raramente. Qualquer
  sistema que anuncie mais está descalibrado ou a mentir. O limiar NÃO será
  baixado post-hoc (seria p-hacking); revisão só em futura versão pré-registada.

---

## REVISÃO v9 — 2026-08-05, pós-investigação profunda (output/research_v9.md)

Regra de decisão aplicada (fixada no plano antes dos resultados): máx. 4 novos
preditores; só com efeito documentado + computável grátis; sem teste no nosso
painel → CONTEXTO, nunca peso.

1. **ENTRA NO TRIBUNAL (testável já)**: `n_events_same_day` (crowding do
   calendário — Hirshleifer-Lim-Teoh: distração modula a reação; DellaVigna-
   Pollet: sexta já coberta pelo dow). Feature nova no painel e no GBM;
   tribunal v9 vs v8 no mesmo harness; adota-se só se melhorar TOP-3/calibração.
2. **CONTEXTO + ARQUIVO (sem histórico grátis → o backtest nasce do nosso
   arquivo)**: CPIV (call−put IV spread ATM ponderado por OI; Atilgan/Lei-Wang-
   Yan), O/S ratio (Johnson-So). Snapshot diário das chains dos candidatos da
   janela guardado em data/chains/ a partir de hoje. Caveat MPP registado:
   ~2/3 destes sinais são borrow fees — short interest FINRA como controlo futuro.
3. **FASES SEGUINTES (documentadas, não implementadas nesta ronda)**: NLP da
   call anterior (Koval ACL'23, 71-77% — o maior efeito encontrado), Lazy
   Prices (diffs EDGAR, 188bps/mês, 100% testável), EMI, Revenue SUE.
4. Validação externa registada: o edge_ratio existente = sinal de Milian 2023
   (t=2,72). O teto de confiança ~60% confirmado como estado da arte por 4
   fontes independentes (Medallion 50,75%; venda de prémio ~58%; academia ~60%).

### ADENDA v9 — tribunal com crowding do calendário (2026-08-05)
GBM v9 (14 features, + n_events_same_day): TOP-1 +4,96%±3,53 | TOP-3 +3,34%±2,41
| spread +0,93pp | Spearman t=1,16 | cobertura conformal 0,796.
vs GBM v8: melhoria em TODAS as métricas (TOP-1 +3,13→+4,96; TOP-3 +3,20→+3,34;
t 1,03→1,16). Regra pré-registada aplicada: v9 ADOTADO (melhor TOP-3).
Continua sem 2-SE → rótulo "heurística" mantém-se (consistente com o teto
documentado no research_v9.md: R² de anúncio ~1% é o estado da arte académico).
Calibração mantém-se excelente nos buckets povoados (24→23; 32→34; 43→45).
Abstenção: 0 sinais ≥0,65 em 5.431 eventos — confirmação definitiva de que o
limiar pré-registado está acima do alcançável com dados públicos.

---

### ERRATA (2026-08-05, auditoria pós-v9)
A adenda v9 diz "14 features"; o código usa **12** (as 8 do kNN + vix, dow,
is_amc, n_events_same_day — `prior_beat_rate` e `prior_skew` estão no painel
mas fora de FEATS). Registado como errata; o histórico não se reescreve.

## REVISÃO v10 — 2026-08-05, registada ANTES do estudo big-winners e do tribunal

Pedido do utilizador: identificar ex-ante os nomes que sobem ≥ +20% no dia do
report ("moonshots"), estudados a 7 anos, e aplicar ao sistema. Projeto movido
para ~/Projects/event_calendar e posto sob git — o commit deste pré-registo
antecede o commit de qualquer resultado (prova de data). REGRAS FIXADAS AGORA:

1. **DADOS**: preços period=10y (antes 3y — era o gargalo real do painel:
   21 meses), earnings limit=100 (antes 30, bucketizado para 50 em 443
   tickers), backfill dos 49 tickers com earnings mas sem preços (NVDA, AMD,
   PLTR, COIN, …). Painel reconstruído (~4-6× eventos esperados). O baseline
   v9 é RE-CORRIDO no painel novo (braço A) — comparar braço B com números
   antigos seria comparar universos diferentes.
2. **LIMIARES (fixos antes de olhar)**: moonshot y ≥ +0,20; cauda simétrica
   y ≤ −0,20 reportada SEMPRE ao lado. Janela primária do estudo:
   event_date ≥ 2019-08-01 (7 anos); painel anterior a isso = contexto.
   Sem otimização de limiar em circunstância alguma.
3. **VIÉS DE SOBREVIVÊNCIA DECLARADO**: o painel 10y nasce do universo de
   HOJE — deslistados/adquiridos 2019-2025 (incl. blow-ups) estão ausentes.
   Todas as taxas-base são CONDICIONAIS a "sobreviveu até 2026"; nenhuma
   afirmação incondicional. Sem mitigação gratuita (dados de delisting não
   são livres); honestidade em vez de correção.
4. **log_mcap**: o look-ahead declarado na v7 (mcap de hoje em eventos
   históricos) AGRAVA-SE a 7-10 anos. No ESTUDO, o eixo de tamanho é
   log_dollar_vol (point-in-time verdadeiro: média 20d de close×volume da
   própria cache); log_mcap aparece só em tabela de contexto com aviso.
   No MODELO, o braço B remove-o (ver 6).
5. **FEATURES CANDIDATAS NOVAS (máx. 2, ambas point-in-time da cache
   existente)**: log_close (nível de preço — efeito lottery/low-price,
   Kumar 2009) e log_dollar_vol (tamanho/liquidez PIT, substitui o papel do
   mcap). REJEITADAS com motivo: n_prior_events (artefacto da janela de
   dados, não idade da empresa); prior_big_up_rate a 20% (com base-rate
   ~4,5% e ≥4 eventos prévios é quase sempre 0 — esparso; a concentração
   repeat-offender mede-se no estudo e, se forte, candidata-se em versão
   futura com estimador encolhido).
6. **TRIBUNAL v10** (harness idêntico: 30 folds ancorados, MIN_TRAIN=800,
   GBM congelado): braço A = 12 features v9 no painel novo (baseline);
   braço B = 13 features = v9 − log_mcap + log_close + log_dollar_vol.
   Exatamente DUAS corridas; sem terceiros braços nem re-tuning.
7. **CABEÇA p_up20_cal**: CalibratedClassifierCV isotónica, target
   y ≥ +0,20, mesmo padrão da p_up5_cal, avaliada dentro dos MESMOS folds.
   SEM limiar de abstenção (lição da v8: limiares acima do alcançável).
   Métricas: curva de calibração; precision@3 diária (dos top-3 diários por
   p20 no teste, fração com y≥+0,20); captura diária (dos eventos de teste
   com y≥+0,20, fração presente nesses top-3).
8. **REGRA DE ADOÇÃO — gates fixados agora** (diferenças EMPARELHADAS por
   fold; SE = std/√F):
   - Gate 1 (não-regressão do primário): média(top3_B − top3_A) ≥ −1·SE.
   - Gate 2 (edge moonshot): captura(p20, braço vencedor do Gate 1) >
     captura(top-3 por p_up5, braço A) E limite inferior Wilson-95 de
     precision@3(p20) > taxa-base agregada de teste (~4-5%).
   - Gate 3 (calibração honesta): todos os buckets p20 com n≥30 têm
     realizado ∈ [0,5×; 2×] do previsto; buckets n<30 publicam-se só com
     aviso de amostra pequena.
   - Decisão: 1∧2∧3 → adota features vencedoras + cabeça p20 + Radar no
     brief · Gate 1 falha → features v9 mantêm-se, cabeça avaliada no braço
     A com Gates 2∧3 · Gate 2 falha → sem Radar · nada passa → modelo
     inalterado e a adenda di-lo. Sem terceiras corridas, sem ajustes.
9. **BRIEF**: secção "Radar +20%" (top-3 por p_up20_cal, probabilidades
   honestas tipicamente 5-20%, aviso bicaudal com o rácio up:down medido no
   estudo, constante datada) SÓ se a cabeça for adotada. CPIV/O·S passam a
   visíveis na tabela EV (contexto, zero peso; caveat MPP mantém-se).
   Aviso automático "amostra pequena" em buckets de calibração com n<30.
   O "n=5.934" hardcoded passa a ler n_scored do ev_validation.json.
10. **ESTUDO (studies/bigwinners.py → studies/bigwinners.md)** — índice
    pré-registado: QA do painel; taxas-base por ano e regime VIX (bins fixos
    <15 / 15-25 / >25); perfis por quartil das features (P(big_up) SEMPRE ao
    lado de P(big_dn)); interação única log_close × prior_avg_move (4×4);
    repeat offenders (P(≥+20% | ≥1 big-up nos 8 prévios)); mecanismo
    (surprise, rotulado "só conhecido após o print"); perfil-lotaria
    pré-declarado = quartil topo de prior_avg_move ∧ metade inferior de
    log_close (P(±20%), rácio up:down, EV bruto sem custos — declarado);
    setor (look-ahead residual declarado). FORA DE ÂMBITO: intraday, NLP,
    histórico de opções (arquivo tem dias), fundamentais PIT, deslistados,
    otimização de limiares.

### ADENDA v10-estudo — resultados (por datar após correr)

### ADENDA v10-tribunal — resultados e decisão (por datar após correr)
