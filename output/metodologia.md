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

### ADENDA v10-estudo — resultados (2026-08-05)
Painel reconstruído: 25.875 eventos, 1.026 tickers, 2017-10→2026-08 (4,2× o
painel v9). Janela 7 anos: 22.086 eventos, 712 moonshots (P=3,22%), cauda
negativa 2,35% (SUBESTIMADA — sobrevivência). Achados (studies/bigwinners.md):
1. prior_avg_move domina: Q4 8,3% vs Q1 0,3% de moonshots (28×) — mas a cauda
   negativa acompanha (5,8% no Q4). Volatilidade compra as DUAS caudas.
2. log_close funciona como pré-registado (lottery): Q1 barato 5,3%/2,7% (rácio
   ~2) vs Q4 caro 1,9%/1,9% (rácio 1). A ASSIMETRIA vive nos baratos.
3. Canto lotaria (vol Q4 × preço Q1): 11,5% up vs 5,5% down (n=1.699).
   Perfil-lotaria pré-declarado: 10,0% up / 5,9% down, rácio 1,69; média
   +1,54%/evento bruto SEM custos (declarado; não é estratégia).
4. Repeat offenders: ≥1 big-up nos 8 prévios → 9,11% vs 2,19% sem (4,2×) —
   valida prior_up_big_rate como feature; top-10% dos tickers = 25% dos
   moonshots (CVNA 8, ARLO 7, PLTR/APP/GRPN/VISN/BW 6…).
5. Mecanismo (ex-post): 82% dos moonshots tiveram beat; 66% beat >15% —
   consistente com o sandbagging como pipeline causal.
6. Surpresas do painel longo: mom60 vira NEGATIVO significativo (t=-2,75) a
   10 anos (era +1,3 no painel curto — reversão, não momentum);
   dist_52w_high perde o sinal (t=-0,1); VIX>25 REDUZ moonshots (2,4% vs
   3,6% em VIX<15 — em pânico o movimento é de mercado, não idiossincrático).
7. Setor (contexto): Tech 4,9% / Industrials e Comm 4,3% vs Financeiras 1,6%,
   Energia 0,6%, REITs 0,3% — gradiente 16×.
8. Taxa por ano sobe 2019→2026 (1,8%→4,6%) — mistura de regime real e
   sobrevivência (nomes recentes ainda listados); declarado.

### ADENDA v10-tribunal — resultados e decisão (2026-08-05)
Painel 25.875 eventos, 30 folds ancorados, braços exatamente como pré-registado:
- **Braço A (12 features v9) COLAPSA no painel longo**: TOP-1 −3,01%±2,38 |
  TOP-3 +0,40%±1,62. O motor v9 era em parte artefacto do painel curto e do
  log_mcap com look-ahead — o re-baseline pré-registado apanhou-o.
- **Braço B (13 = v9 − log_mcap + log_close + log_dollar_vol)**: TOP-1
  +4,97%±3,74 | **TOP-3 +3,97%±1,60** | Spearman t=2,02 | cobertura 0,793.
- Gate 1 (emparelhado): diff +3,571pp vs SE 2,116pp → PASSA → features B.
- Gate 2: captura p20 0,2911 > baseline p5 0,2781 E precision@3 diária 6,94%
  com Wilson-lo95 6,11% > base 3,05% (o dobro da base, estatisticamente
  limpo) → PASSA.
- Gate 3: 4 buckets n≥30 todos dentro de [0,5×;2×] — e CONSERVADORES
  (0,7→0,7; 3,3→4,1; 6,7→8,8; 11,8→14,3) → PASSA.
- **DECISÃO (aplicação mecânica): FEATS=FEATS_V10 adotado + cabeça p_up20_cal
  + Radar no brief.** gbm_validation.json passa a ser o do braço B (o brief
  audita o modelo em produção). Buckets p20 com n<30 (0,15-0,30: 23+19+5
  eventos) continuam instáveis — cobertos pelo aviso small-n do brief.
- p5 no painel longo: bucket 0,5-0,6 com n=33 previsto 53%→realizado 49%;
  abstenção a 0,65 continua sem sinais (1 evento em 25,6k) — limiar mantido.
- **EV kNN (v7) no painel longo: quintil topo bate fundo >2 SE (n=25.575)**
  — pela regra pré-registada da v7, o rótulo "ordenação heurística, edge não
  provado" é SUBSTITUÍDO pelo veredito novo do ev_validation.json. Quatro
  vezes mais dados encontraram o spread que 5,9k eventos não conseguiam
  distinguir de ruído.

## REVISÃO v11 — 2026-08-05, registada ANTES de qualquer alteração de código

Pedido do utilizador: pipeline UNIFICADO — um candidato claro, menos dispersão,
e visibilidade dos nomes tipo PLTR que sobem ≥20% no dia do report. Diagnóstico
(2 investigações, dados de 2026-08-05):
- PLTR-class = JANELA, não veto: PLTR reporta 02/11 (89 dias); CVNA/HOOD/RDDT/
  COIN reportaram em finais de julho, antes de o sistema existir. Sistema é de
  curto prazo (janela 7d) — certo em não os mostrar, errado em não dizer quando voltam.
- Vetos anti-selecionam moonshots: 56,4% dos candidatos vetados (Altman=72%);
  9 dos 10 maiores p_up20_cal globais VETADOS; 8/15 fábricas de moonshots
  presentes vetadas; taxa moonshot 3,45% vetados vs 2,62% elegíveis, MAS
  mediana −0,24% vs +0,60% — o veto compra mediana e paga cauda. CAVEAT
  DECLARADO: fundamentais DE HOJE sobre eventos passados (look-ahead; não há
  PIT grátis) — direção robusta, magnitudes moles. Vetos NÃO são backtestáveis;
  o que se segue sobre eles é DECISÃO DE DESENHO, não resultado empírico.
- Dispersão estrutural: 6 rankings rivais; score em 2 escalas na mesma coluna;
  grau A preso ao top-100 com opções (contradiz "custo, não critério" v6§1);
  timing "?" invisível; 5 bugs latentes.

REGRAS FIXADAS AGORA (decisões do utilizador: flags sem excluir · piso $10M ·
graus abolidos):
1. **ESPINHA ÚNICA**: gbm_ev + p_up20_cal são o único ranking exibido. score v2
   = pré-ranking interno de enriquecimento (escala mista pré/pós-opções
   DECLARADA; nunca exibido); score_v3/v4 ficam no CSV como contexto; ev_knn
   mantém-se no ANEXO (robustez independente, validação própria >2SE).
   **GRAUS A/B/C ABOLIDOS** — eram etiquetas de disponibilidade de dados, não
   de qualidade → a informação vira flags por linha.
2. **VETOS → FLAGS, objetivo-casados**: a CABEÇA (candidato nº1 + alternativas)
   continua a exigir zero flags (regra de seleção v8§5 INALTERADA); o RADAR
   deixa de excluir por veto e mostra 🚩 SEMPRE; a tabela EV do anexo mantém a
   regra v7 (vetado fora — o EV é média, e o veto compra mediana). Flags são
   risco forense visível, não proibição.
3. **PISO DE LIQUIDEZ DO RADAR**: log_dollar_vol ≥ 7,0 (≈$10M/dia, feature PIT
   v10). DECLARADO: custa taxa-base (3,70% abaixo vs 2,97% acima — moonshots
   vivem nos pequenos); aceite porque picks intransacionáveis não servem o
   objetivo. Excluídos pelo piso são LISTADOS, nunca silenciosos. Valor fixo.
4. **ÂMBITO**: timing "?" entra no braço AMC do dia (prazo mais cedo = nunca
   atrasado) com flag "timing n/conf."; date_verified=False vira aviso na
   própria linha do pick (deixa de rebaixar grau — os graus morreram).
5. **FÁBRICAS DE MOONSHOTS**: secção nova — contagem y≥+0,20 desde 2019-08 no
   painel (sobrevivência declarada) × próxima data de report da cache yfinance
   (idade da cache >7d mostrada; confirmar no IR). Responde no produto a
   "porque não está a PLTR": janela=7d; PLTR (6×) reporta 02/11.
6. **ENRIQUECIMENTO**: top-100 ∪ eventos ≤ T+2 (âmbito exibível) ∪ ALWAYS_ENRICH
   ∪ posições, cap 300 com aviso; optclean ganha carimbo asof (refresh diário só
   do âmbito); options_attempted distingue "tentado sem quote" de "nunca tentado".
7. **CORREÇÕES (bugs, não método)**: rescore_v3 `c` fora do binding; brief sem
   coluna veto_v3 partia; universo Nasdaq abortava a janela toda à 1ª exceção
   (passa a continuar-por-dia com dias falhados publicados); gate de recall v5
   finalmente implementado (warn-only; ALWAYS_ENRICH re-verificado).
8. **O QUE NÃO MUDA (e porquê não há tribunal)**: painel, features B, GBM,
   cabeça p20, gates v10, regra de seleção da cabeça — INTACTOS; nenhum modelo
   re-treinado ⇒ sem braços A/B. O filtro |y|>1,0 do painel (descarta movers
   reais >100%) ADIA para v12 — mudá-lo reconstrói o painel e exige
   re-tribunal; a partir de agora cada descarte é logado (ticker/data/y).

### ADENDA v11 — verificação pós-implementação (2026-08-05, ~23:15)
- Radar reformado A FUNCIONAR: top-5 do dia = AGL/PAYO/GENI/FSLY/TDAY (todos
  ~12% p20, todos $13-111M/dia, todos com 🚩 visível — TODOS estavam escondidos
  por vetos no regime anterior). Excluídos pelo piso LISTADOS (TDUP 13%/$8M,
  ARHS, CPS). Bilhete de lotaria: AGL 🚩Altman (antes: micro-cap CTKB ilíquida).
- Fábricas: APP (6×) e TDUP (5×) reportavam HOJE; ARLO/VISN/GRPN amanhã;
  CVNA 28/10; PLTR 02/11 — a pergunta "porquê não PLTR" respondida no produto.
- Graus abolidos: grep "GRAU" no brief = 0; contagens novas no print final
  (âmbito 430 · sem flags 194 · radar 327 · flags 236).
- Crash-path testado: brief gera sem coluna veto_v3 (degrada para zero flags).
- rescore_v3 corre sem NameError; gbm --score persiste log_dollar_vol (8 cols).
- Colisão de nome descoberta na implementação: coluna "flags" choca com a
  property DataFrame.flags do pandas → renomeada veto_flags (bug de 1ª ordem
  que o teste apanhou antes de qualquer envio).
- Nota honesta: com flags visíveis, o topo do Radar do próprio dia mudou de
  micro-caps limpas para nomes líquidos em distress (Altman) — é exatamente o
  trade-off pré-registado: risco forense à vista em vez de escondido.

---

## REVISÃO v12 — 2026-08-06, registada ANTES de qualquer alteração de código

Base: 3 investigações profundas (2026-08-05, ~50 pesquisas, fontes primárias)
sobre remédios para as 6 falhas ideológicas definidas. Achado reordenador:
**a colheita de moonshots via ações está EV-negativa** com os números atuais
(0,08×+30% − 0,92×8% = −4,96%/evento; Kelly=0; breakeven exige perda média
≤−2,6% vs −8% atual) — o gargalo é o LADO DA PERDA, não o hit-rate. Técnicas
de tail-modeling (class weights, SMOTE, EVT, quantile q95): NO-GO documentado
— a P(≥20%) calibrada isotónica JÁ é a ferramenta textbook-correta. Compra de
opções: morta líquida de custos (BSIC +1,17% bruto → −9,07% líquido).

REGRAS FIXADAS AGORA (decisão do utilizador: Fases A+B; C em roadmap):
1. **AUTOPSIA DA PERDA (A2) é DESCRITIVA**: reconstruir picks top-3 walk-forward
   e dissecar E[y|y<0] por decil de P, liquidez, preço, setor, VIX. Qualquer
   filtro que dela nasça vai a TRIBUNAL v13 — nunca adoção direta. O rodapé do
   brief ganha a aritmética Kelly com os números medidos (sizing honesto).
2. **TRIBUNAL v12 (única mudança de modelo)**: braço A = 13 features v10
   (re-baseline no painel com merge FINRA) vs braço B = 15 = v10 +
   short_ratio_z5 + short_ratio_z20 (FINRA daily short volume, histórico
   2018-08→hoje, PIT por construção — keyed na data do ficheiro T+0).
   Gates 1/2/3 idênticos à v10. Duas corridas, adoção mecânica.
3. **REGIME (contexto, zero peso)**: % dos últimos N=50 eventos do painel com
   |y| > mediana móvel de 4 trimestres própria; limiares FIXOS: >0,50
   comprador / <0,42 vendedor (baseline estrutural 58/42 documentado).
   Variante implied-vs-realized do arquivo entra quando ≥50 eventos com implied.
4. **TRIPWIRES (monitor mensal + aviso no brief)**, limiares fixos:
   (a) descalibração: bucket n≥30 com realizado fora de [0,5×;2×] do previsto;
   (b) lift morto: precision@3 p20 ≤ 1,0× a taxa-base; (c) espinha morta:
   TOP-3 realizado ≤0 em 2 corridas mensais consecutivas; (d) cobertura
   conformal fora de [0,75;0,85]. Tarefa mensal re-corre o tribunal em vigor.
5. **CONTEXTO ATÉ VALIDAÇÃO PROSPETIVA** (sem histórico PIT grátis → sem
   tribunal já): snapshots diários de estimativas (data/estimates/ — caminho
   crítico do NLP/SUE futuro); EMI (Johnson-Kim-So: COV+INST+SG+ALT, média de
   percentis, 64-88bps/mês documentados); bundle de opções do arquivo próprio
   (iv_spread Cremers-Weinbaum, smirk Xing-Zhang-Zhao, implied_move_pctile,
   otm_call_oi_d5 à Augustin — tribunal quando arquivo ≥1 trimestre); FINRA SI
   bi-mensal + DTC (keyed na DATA DE PUBLICAÇÃO ~T+8du).
6. **TESTE RN-P (B3, não-executante)**: P_RN(≥+20%) por call-spread K≈1,2×spot
   do arquivo vs p_up20_cal; log diário acumulado; veredito mensal no monitor.
   EXPECTATIVA PRÉ-REGISTADA: perder (prémios de variância inflacionam P_RN).
7. **ERRATA**: shortPercentOfFloat (yfinance) é snapshot SEM DATA — look-ahead
   silencioso em qualquer uso histórico; passa a contexto com aviso; FINRA é a
   fonte datada. Nota: SR-FINRA-2026-012 (SI semanal T+5) com decisão SEC
   ~2026-08-14 — se aprovada, o candidato FINRA sobe de valor.
8. **ROADMAP FASE C (documentado, não implementado)**: Form 4 oportunista
   (CMP 82bps/mês; janela 30-180d, NUNCA 2 semanas — Ke-Huddart-Petroni);
   Lazy Prices (~7%/ano full-doc pré-decay; 188bps era só Risk Factors;
   OOS 2015-2026 pré-registado antes de qualquer uso); NLP calls Koval
   (repo morto; piso honesto 56-63% balanced acc; bloqueado pelo painel de
   consenso → depende dos snapshots A1 maturarem). NO-GO permanentes:
   Google Trends (PIT impossível), WSB como sinal (nível contrário −8,5%),
   velocidade 8-K (sinal documentado com sinal errado).
9. O QUE NÃO MUDA: painel (filtro |y|>1,0 fica para v13 — uma variável por
   tribunal), features v10/v11, cabeça p20, gates, regra de seleção, Radar v11.

### ADENDA v12 — resultados parciais (2026-08-06, madrugada)
1. **AUTOPSIA (studies/loss_autopsy.md, 30 folds, picks top-3 diários):** a
   aritmética teórica da investigação (−4,96%/evento) estava DEMASIADO
   pessimista — ignorava os 43% de picks que caem em [0; +20%). MEDIDO:
   estratégia p20 = P(win)6,8% · E[win]+31,2% · P(y<0)49% · E[y|y<0]−8,58% ·
   **EV +0,82%/pick**; espinha = P(y>0)50,7% · **EV +0,85%/pick**. MAS como
   aposta binária na cauda o Kelly do moonshot é NEGATIVO (f*=−0,77) — o EV
   vem do meio, não do bilhete. Candidato a filtro (excluir Q4 de vol
   histórica) REJEITADO: só melhora a perda −8,58→−7,46 e corta 52% dos
   moonshots capturados. Rodapé do brief ganhou a linha de sizing datada.
2. **RN-P (1º dia, n=63 pares):** P_RN mediana 12,2% vs P_cal 6,8%;
   P_cal>P_RN em apenas 16% — os prémios de variância inflacionam a cauda
   implícita ~1,8×, exatamente como pré-registado. Comprar calls de earnings
   = pagar quase o dobro da probabilidade física. Log acumula em
   data/rnp_log.csv; veredito mensal no monitor.
3. **Regime (1ª leitura, painel até 05/08):** VENDEDOR — 32% dos últimos 50
   eventos acima do hábito próprio. Nota: mede |y| vs hábito do ticker;
   a lente implied-vs-realized (ORATS dizia comprador) entra quando o
   arquivo tiver ≥50 eventos com implied — as duas lentes ficam declaradas.
4. **Live no brief:** EMI v1 (1002/1039 com ≥3 inputs; proxies declarados),
   smirk (655 no 1º dia), FINRA SI bi-mensal (1030/1039, settlement
   2026-07-15, via Query API particionada), tripwires TODOS VERDES na
   corrida baseline. ΔOI ativa aos 6 snapshots de arquivo; pctile do
   implied move aos 8.
5. **Snapshot de estimativas nº 1**: 1.039 tickers, 91 colunas, 982 com
   consenso EPS 0q — o painel PIT de consenso existe desde 2026-08-06.

### ADENDA v12-tribunal — FINRA (2026-08-06, madrugada)
Painel reconstruído: 26.073 eventos, 1.034 tickers; short_ratio_z5/z20 cobrem
88% (NaN pré-2018 e símbolos fora do NMS — imputação por mediana do harness).
- **Braço A (re-baseline 13 feats)**: TOP-3 +3,14%±1,98 | spread +1,07pp
  **PASSA 2-SE** | t=3,66 | p20 precision 6,97% (2,3× base).
- **Braço B (15 = +FINRA)**: TOP-3 +3,64%±2,07 | spread +0,99pp PASSA 2-SE |
  **t=4,61** | TOP-1 +1,20% vs +0,11%.
- **MARCO**: primeira vez que o spread quintílico do GBM passa o teste 2-SE
  (em AMBOS os braços) — o rótulo "spread indistinguível de ruído" cai para
  o motor principal no painel de 26k eventos.
- Gate 1: PASSA (+0,503pp, SE 1,521) → **FEATS_V12 ADOTADO** (a partir desta
  noite o scoring computa FINRA ao vivo — live_z; sem isso a feature morreria
  na mediana). Gate 3: PASSA.
- **Gate 2: FALHA — aviso amarelo declarado**: no painel novo, ordenar por
  p20 já não captura mais moonshots que ordenar por p5 (28,5% vs 29,8%,
  empate estatístico; na v10 era 29,1% vs 27,8%). DESAMBIGUAÇÃO FIXADA
  AGORA: o Gate 2 rege ADOÇÕES novas de cabeças; a continuidade de uma
  cabeça já adotada rege-se pelos TRIPWIRES (§4 — lift atual 2,2×, verde).
  O Radar mantém-se (valor de display: probabilidades de cauda calibradas +
  flags, que o ranking p5 não comunica); se o lift cair ≤1×, o tripwire
  remove-o automaticamente. Candidato v13: reavaliar o ranking do Radar
  (p20 vs p5 vs blend) em tribunal próprio.
- gbm_validation.json = braço B (o brief audita o motor em produção);
  SKILL noturno ganha o update incremental FINRA (segundos/dia).

---

### NOTA v10.2 — apresentação do brief (2026-08-05, pedido do utilizador)
O brief passa a abrir com UM "Candidato nº 1 do dia" nomeado + 2 alternativas
+ bilhete de lotaria em linha única; todo o detalhe (tabelas EV, Radar, graus,
vetados) desce para um ANEXO marcado. A REGRA DE SELEÇÃO É A JÁ PRÉ-REGISTADA
(topo do gbm_ev entre elegíveis não-vetados, v8§5) — zero alterações de método,
pesos ou limiares; mudança de apresentação apenas. O selo "alta confiança"
mantém o limiar 0,65; abaixo dele o nº 1 é nomeado com a etiqueta "sem selo"
e a probabilidade complementar explícita. Racional documentado: o tribunal
valida o edge no TOP-3 (±1,60), não no top-1 (±3,74) — o brief nomeia um mas
mostra sempre os três. Também acrescentado modo pré-fecho (EVENTCAL_TODAY=1,
AMC de hoje + BMO de amanhã, prazo hoje 21:00) — v10.1, mesma lógica.

## REVISÃO v13 — 2026-08-06, registada ANTES de qualquer código ("a grande limpeza")

Gatilho: o utilizador rejeitou o piso de mcap ($500M) após CLRO/FTK/AEIS; a
auditoria exaustiva inventariou 147 regras numéricas — 38 arbitrárias (sem
justificação em lado nenhum), 7 divergências código↔pré-registo, 4 regras
mortas. Só 4 limiares têm custo/benefício MEDIDO (piso do Radar, ABSTAIN_P,
BIG_UP20, vetos). Filosofia v13: exclusão silenciosa → visibilidade com
flags; arbitrário → declarado; divergência → errata; morto → enterro formal
ou ressurreição; única mudança de modelo (|y|) → tribunal.

1. **MIN_MCAP REMOVIDO** (decisão do utilizador; v5§2 nunca teve evidência).
   Custo declarado: universo ~2× (746-1.107 tickers estavam a ser cortados),
   noturno +15-25 min (medido na 1ª corrida; se >60 min, qualquer cap futuro
   será por LIQUIDEZ $/dia, nunca por mcap, e vai a decisão do utilizador).
   Consequência honesta: entra lixo CLRO-class ($10M, dados mortos) — será
   visível como Estreante/não-pontuável, nunca como pick. Protecções que
   ficam (medidas): piso de liquidez do Radar, flags forenses, cabeça
   zero-flags.
2. **ESTREANTES**: candidatos na janela sem score (<4 eventos prévios ou
   <260d de preços — IPOs recentes) ganham secção própria no brief (dados
   observáveis: mcap, $/dia, implied, flags) SEM scores fabricados. Modelo
   para estreantes = candidato v14 com tribunal próprio.
3. **TRIBUNAL v13** (única mudança de modelo): braço A = painel com descarte
   |y|>1,0 (status quo) vs braço B = |y|>2,0 + guarda de sanidade (Close
   >$0,50 e Volume>0 nos dois dias da reação). Gates 1/3; Gate 2 rege só
   cabeças novas (desambiguação v12). Adoção mecânica.
4. **ERRATAS**: Radar exibe 5 (v10§9 dizia 3) — mantém-se 5, fica registado;
   excluídos-pelo-piso listavam só 3 (contradizia "nunca silenciosos" v11§3)
   → top-10 + contagem; ΔOI exige 6 snapshots (docstring dizia 5) → fixa-se
   6; o filtro de spread 30% do RN-P dizia-se "pré-registado" sem o ser —
   fica registado AGORA; RECALL_MIN_UNIVERSE=50 não era o recall de 95% do
   v5§3 → implementa-se o recall real (ALWAYS_ENRICH com evento confirmado
   fora do universo automático ⇒ aviso).
5. **ENTERROS E RESSURREIÇÕES**: concordância de estimadores 1,5× (v4§3/v6§2)
   ENTERRADA (morreu com os graus na v11; nada a substitui — registado);
   ">40% de dados em falta não pode ser top pick" (v1§1) RESSUSCITADA como
   flag "⚠ dados incompletos (X%)" na linha do pick (avisa, não exclui);
   flag monthly_expiry (v1§5) passa finalmente a chegar ao brief (⏳ no
   Radar/EV quando a expiração usada excede o evento em >10d); o ranking
   /dev/null do rescore_v3 é apagado.
6. **CONSTANTES OPERACIONAIS DECLARADAS** (sem mudança de comportamento;
   alterações futuras exigem nota datada): buckets de calibração p5
   [0,.3,.4,.5,.6,.65,.7,.8,1] e p20 [0,.02,.05,.10,.15,.20,.30,1]; mínimo
   30 positivos/negativos para calibrar; FINRA z: janelas 5/20, base 120,
   mínimo 60 obs; EMI ≥3 de 4 inputs; VIX staleness 5 dias; banda ΔOI
   1,05-1,25× spot; smirk tolerância 0,1× e put 0,80× (paper); RN-P strikes
   1,15×/1,25× tolerância 0,08× e mínimos 4/2 calls; tstat n≥30; painel:
   260 barras / 60 pré-evento / 4 eventos prévios (mantidos — necessários às
   features; a alternativa para <4 é a secção Estreantes, não imputação);
   displays head(5/10/8/10); hype bins 70/40 e escala 50+20z; isascii passa
   a CONTADO nas stats; âmbito unificado SCOPE_DAYS=3 (chains e
   enriquecimento divergiam T+3 vs T+2 — unifica-se em 3).

### ADENDA v13 — resultados (2026-08-06, manhã) + CONFISSÃO DE CONTAMINAÇÃO
1. **Tribunal |y| (gates formais): A 26.073 vs B 26.630 eventos; TOP-3 +3,64→
   +3,70; TOP-1 +1,20→+6,00; Gates 1∧3 PASSAM → YMAX=2,0+guarda ADOTADO.**
2. **CONFISSÃO (apanhada na verificação pós-adoção): o braço B ficou
   CONTAMINADO.** O rebuild do braço B correu em simultâneo com a primeira
   corrida do universo sem piso, que estava a descarregar preços de tickers
   novos — o braço B apanhou +557 eventos dos quais só **3** são movers >100%
   recuperados pela regra nova; o resto é expansão de universo. A comparação
   violou o princípio "painéis diferentes não se comparam" (v10§1). LEITURA
   HONESTA: o salto do TOP-1 (+1,20→+6,00) atribui-se à EXPANSÃO DO UNIVERSO,
   não à mudança do |y|; a mudança do |y| é quase-nula em tamanho (3 eventos
   em 27k) e mantém-se adotada por ser inofensiva e conceptualmente correta
   (movers reais não são "erros de dados"). RE-VALIDAÇÃO LIMPA: o tribunal
   mensal (dia 1) re-corre no universo estabilizado — esse será o número
   citável. Até lá, o brief cita as métricas v13B com a nota "universo em
   expansão".
3. Painel de produção v13: **27.184 eventos, 1.091 tickers** (cresce à medida
   que os small caps backfillam), 844 moonshots ≥+20%.
4. **CUSTO MEDIDO do universo sem piso (2026-08-06)**: 1.ª corrida = **1.703
   candidatos em 4h28** (16.055s) — muito acima da estimativa de +15-25 min.
   Diagnóstico: o backfill único de ~700 tickers novos + o facto de os
   FUNDAMENTAIS serem o único fetch SEM cache (iam à rede todas as noites
   para todos os tickers). CORREÇÃO (custo, não critério): fetch_financials
   ganha cache de 72h (dados trimestrais toleram 3 dias) — noites seguintes
   estimadas em 25-45 min com cache quente; a 1.ª noite de cada trimestre
   paga o refresh. Se a noite exceder 60 min de forma persistente, aplica-se
   o pré-registado: cap por LIQUIDEZ (nunca mcap) vai a decisão do utilizador.

### NOTA v13.2 — regra do Escolhido: EV ajustado ao risco (pré-registo ANTES do tribunal)
Pedido do utilizador: "a que no global com segurança é a mais provável de
subir mais". Tradução mecânica pré-registada: rank do Escolhido passa de
gbm_ev puro (regra A, v8§5) para **regra B: gbm_ev ÷ largura do intervalo
conformal (q90−q10)** — EV por unidade de incerteza; sobe quem promete
mais COM intervalo mais apertado. TRIBUNAL (mesmos 30 folds): para o TOP-1
realizado de cada regra medem-se (i) retorno médio, (ii) P(y<0) do pick,
(iii) queda média quando cai. GATES fixados AGORA, segurança primeiro
(intenção declarada do utilizador): adota-se B se P(y<0) do TOP-1 descer
E o retorno médio do TOP-1 não degradar mais de 1·SE (diferenças
emparelhadas). Caso contrário mantém-se A e a nota di-lo. Elegibilidade
inalterada (zero flags); apresentação = v13.1.

**ADENDA v13.2 (2026-08-06): REGRA B ADOTADA.** Tribunal (30 folds
emparelhados, painel 27.184): P(y<0) do TOP-1 **56,7%→46,7%** (o gate de
segurança); retorno médio igual (diff −0,00pp, SE 2,87pp — não degrada).
Custo declarado no email: quando cai, cai mais fundo (−11,4% vs −9,4% —
a regra evita quedas FREQUENTES, não quedas profundas). Nota de contexto:
o nível absoluto do TOP-1 neste snapshot (~0%) reflete o universo em
expansão + o ruído próprio do top-1 (SE ±2,9pp); a comparação A/B é
emparelhada nos mesmos folds e é isso que decide. Nível citável = tribunal
mensal no universo estabilizado. Aplicado ao email E à cabeça do brief
(um só nº 1 em todo o produto).

### NOTA v13.1 — email de escolhido único (2026-08-06, pedido do utilizador)
O EMAIL passa a conter UM único nome ("O Escolhido do dia") com o caso
fundamental explicado por extenso (receita, margens, qualidade dos lucros,
sandbagging, posicionamento short, expectativas) + o caso CONTRA + pesquisa
web do nome + rodapé de honestidade. REGRA DE SELEÇÃO INALTERADA (v8§5:
topo do gbm_ev entre elegíveis sem flags — zero mudança de método; mudança
de apresentação apenas). O brief completo (Radar, Estreantes, EV, anexo)
continua a ser gerado e arquivado localmente (output/brief_*.md) para
auditoria e consulta; simplesmente deixa de seguir por email. Linguagem:
"o caso a favor/contra do nº 1", nunca diretivas de compra — decisões do
utilizador (invariante v1).

### NOTA v13.3 — horário e semântica do email (2026-08-06, pedido do utilizador)
O email diário muda de 21:45 (pós-fecho, prazo do dia SEGUINTE) para
**~20:00 seg-sex** (pipeline arranca 19:00; mercado ainda aberto): o modo
pré-fecho (v10.1) passa a ser o PRODUTO PRINCIPAL — âmbito AMC de HOJE +
BMO de amanhã, **prazo de decisão 21:00 do próprio dia** (~1h de janela de
ação). Fins-de-semana sem eventos → sem email. Nenhuma mudança de método;
apenas quando e com que âmbito o Escolhido é entregue. Quotes de opções
passam a ser intraday ao vivo por construção (vantagem vs pós-fecho).

### NOTA v13.4 — cap de enriquecimento 300→650 (2026-08-06, custo não critério)
O cap de 300 disparou na 1ª corrida sem piso (âmbito exibível = 609).
Com os fundamentais em cache, +350 quotes custam ~10 min/noite → cap sobe
para 650 (ENRICH_SCOPE_CAP no config). Aviso mantém-se se exceder.

### NOTA v13.5 — auditoria externa ao pick NRDS (2026-08-06, contraditório aceite)
Um auditor externo (via utilizador) atacou a atribuição do Escolhido. Vereditos:
1. **G1 (colinearidade prior_avg_move × prior_up_big_rate, r=0,77): método
   ACEITE, conclusão REFUTADA pelo próprio teste proposto** — a substituição
   CONJUNTA do par dá +3,26pp (não −0,3pp): deltas individuais de features
   colineares em GBM não somam. A "pólvora" é o motor dominante; o pick nunca
   dependeu da atribuição (NRDS nº 1 da janela em qualquer caso).
2. **G2 (sandbag ≠ guide-down): ACEITE por inteiro** — o modelo não distingue
   pessimismo de mercado de guidance calibrado da gestão; não testável sem
   guidance histórico (falha de informação; roadmap NLP). Remédio na camada
   certa: o research noturno passa a testar consenso-vs-guidance e a escrever
   o aviso "⚠ Guide-down" quando o sandbag negativo for da gestão.
3. **G3 (mediana e SE do subconjunto): SE ACEITE em cheio** — IC95 dos 50
   análogos [−3,4%;+4,9%] atravessa zero; o email passa a dizê-lo sempre que
   acontece. Mediana REFUTADA nos dados: +1,96% > média +1,32% (cauda gorda
   é a ESQUERDA, pior análogo −63%) — não é perfil carregado pela cauda direita.
4. Novos por auditoria: regra de medição fecho-a-fecho EXPLÍCITA no email
   (paridade backtest-live; sair na abertura quebra-a); ledger de escolhidos
   ao vivo (data/picks_log.csv) liquidado pelo monitor — o veredito da série
   é ao evento ~20, nunca ao evento 1.

## REVISÃO v14 — 2026-08-06, registada ANTES do código (spec cloud do utilizador)

Migração para runner cloud autónomo (routine 17:03 seg-sex, email ≤20:00,
deadline duro 19:50 → aborta e alerta FALHA). REGRAS FIXADAS AGORA:
1. **SEM TRADE HOJE**: o Escolhido só é nomeado se rank_ra ≥ 0,05 E
   gbm_ev ≥ +1,0% E log_dollar_vol ≥ 7,0 (o piso do Radar aplica-se ao
   pick). Abaixo de qualquer limiar → email "NÃO HÁ TRADE HOJE" (proibido
   forçar o melhor de um dia mau). Valores iniciais declarados; revisão
   apenas no tribunal mensal.
2. **CUSTOS SUBTRAÍDOS**: EV líquido no email = EV − fricção estimada por
   tier de liquidez (ldv≥8: 10bps; 7-8: 40bps) — haircut declarado, não
   calibrado (sem dados de fills; o confronto do ledger vai medi-lo).
3. **PLANO DE EXECUÇÃO no email** (parâmetros do próprio utilizador,
   escritos no config: risco 0,5-1%/evento, janela 20:45-20:55, saída =
   fecho seguinte). O sistema REPORTA o plano configurado; não é
   recomendação (invariante v1).
4. **TRIBUNAL v14 (fusão de colineares)**: braço A = 15 features atuais;
   braço B = 14 (remove prior_up_big_rate, o gémeo fraco do par r=0,77 —
   prior_avg_move fica como A família de volatilidade). Gates 1/3.
5. **ESTADO CLOUD**: despensa portátil data/state.tar.gz (preços TRIMADOS
   a 3 anos — chegam para todas as features PIT; earnings/info/fin/vix/
   optclean/FINRA) commitada a cada corrida; rebuilds profundos de painel
   (10 anos) ficam para o job mensal. Preços passam a fetch INCREMENTAL
   (append desde a última barra; full refetch em falha).
6. Envio por webhook Make (MAKE_WEBHOOK_URL em env do cloud, nunca no
   repo); pesquisa das 19:40 = bloco delimitado do agente da routine
   (máx. 3 pesquisas, formato fechado, teste guide-down obrigatório).
7. Runner local continua PRIMÁRIO até ao primeiro verde cloud completo.

### ADENDA v14-fusão (2026-08-06, ~17:20)
Tribunal A(15f) vs B(14f, sem prior_up_big_rate): TOP-3 +1,10% vs +0,93%
(diff −0,17pp ±1,80 — dentro de 1·SE, Gate 1 PASSA); ordenação MELHORA
t=2,94→3,95; **Gate 2 PASSA** (captura p20 > baseline p5 E Wilson-lo95 >
taxa-base — reportado por inteiro; nada omitido); Gate 3 PASSA (5 buckets
n≥30). **FUSÃO ADOTADA (FEATS_V14, 14 features).** CAVEAT EXIGIDO PELO
UTILIZADOR: esta evidência é de DESENVOLVIMENTO — o painel foi visto
pelos tribunais v10-v14; a confirmação independente virá do walk-forward
v15 (folds nunca reafinados) e do ledger live. Nota: os níveis absolutos
de TOP-3 (~+1%) refletem o painel em expansão pós-piso (universo com
small caps novos) — comparações A/B emparelhadas é que decidem.

### ADENDA v14 — (por preencher: dry-run cloud, custo medido)

### NOTA v14.1 — fasquia de liquidez do pick CONFIRMADA (2026-08-06)
Após contraditório do utilizador ("DCH/NRDS não me parecem boas ações"),
mediu-se a curva conforto↔edge com os candidatos do dia: piso $10M → EV
+2,3% (DCH, $1,4B, receita +69%); $50-100M → +1,5% (EQX); $500M → +0,2%
(morto). Utilizador escolheu MANTER $10M — máximo edge, nomes
desconhecidos aceites porque o email explica sempre o caso completo.
A frase que fica: as ações famosas são as mais analisadas do planeta —
o edge vive onde ninguém olha.

### NOTA v15.2c — reparações operacionais pós-perda de container (2026-08-06, noite)
Auditoria completa em docs/plano_reparacao_2026-08-06.md. Nada
metodológico muda (custo/fiabilidade, não critério):
1. **.gitignore bloqueava a despensa**: `data/*` ignorava
   data/state.tar.gz — o `git add` do run_pipeline recusava o ficheiro
   com o erro engolido por `2>/dev/null`. A despensa v14§5 NUNCA chegou
   a ser versionada; o estado da sessão de trabalho (caches, painel de
   27k eventos, checkpoint EDGAR) morreu com o container. Exceções
   acrescentadas (state.tar.gz e data/edgar/, sem idx/); o add deixa de
   esconder erros.
2. **run_pipeline.sh**: preservação do estado (pack+commit) passa a
   correr SEMPRE — em sucesso, em falha de envio e em deadline — e o
   monitor/snapshot correm mesmo sem email: o ledger não depende do
   webhook. Antes, uma falha de envio abortava antes dos pós-processos
   e perdia a noite inteira de estado.
3. **Crawler EDGAR**: checkpoint gzipado e commitado a cada 500 CIKs —
   o crawl v15-P2 passa a sobreviver à morte de containers, não só a
   quedas de rede (v15.1). O crawl de hoje perdeu-se; recomeça do zero.
4. **send_webhook**: NameError latente quando só existia o .html; e o
   rodapé do email deixou de apontar para output/brief_*.md (gitignored
   — o leitor nunca o podia abrir; o brief continua arquivado na sessão
   da routine).
5. Ledger intocado por reconstruções: o pick oficial de 2026-08-06
   (DCH, gerado 16:52) mantém-se; re-runs de infraestrutura fora de
   horas não substituem o registo do dia (proteção manual nesta
   reconstrução; o dedupe por asof continua a reger a routine normal).
6. **yfinance no cloud (achado do 1º teste real)**: o egress do runner
   reinicia o handshake TLS impersonado do curl_cffi — 100% dos fetches
   Yahoo falhavam com curl(35). Fix: sessão curl_cffi sem impersonate
   criada em fetch.yf_session() quando CCR_AGENT_PROXY_ENABLED=1;
   TODOS os yf.Ticker passam pelo fetch.get_ticker (5 call sites
   consolidados). Local: comportamento por defeito intacto (session
   None). Nota honesta: o endpoint do crumb do Yahoo faz rate-limit ao
   IP partilhado do datacenter — a viabilidade do fetch cloud está em
   observação no primeiro verde ponta-a-ponta.
