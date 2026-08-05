# DOSSIER DE INVESTIGAÇÃO PROFUNDA v9 — 2026-08-05

*4 agentes paralelos, 10-16 pesquisas cada + leitura direta de papers.
Compilado por ordem de chegada; síntese final no fim.*

---

# RELATÓRIO C — SINAIS DE OPÇÕES (16 pesquisas + 6 fetches + 2 PDFs lidos)

A investigação está completa — 16 pesquisas web + 6 fetches + leitura direta de 2 PDFs académicos (RFS 2019 e JRFM 2023). Segue o relatório final em português europeu.

---

# Preditores de Reações a Resultados Baseados em Opções — Mapa Completo da Literatura com Effect Sizes

**Data:** 2026-08-05 · **Âmbito:** o que as cadeias de opções (implementáveis via yfinance) prevêem sobre o anúncio de resultados que se aproxima. Números apenas de fontes verificadas; incertezas marcadas **NÃO VERIFICADO**.

## Síntese executiva

A literatura divide-se em dois eixos: **(i) magnitude** (o implied move e a term structure prevêem a variância realizada do anúncio extraordinariamente bem — correlação transversal ≈85% — mas com um prémio de risco médio de ~80 pb de volatilidade que favorece vendedores *através* do evento e compradores *antes* do evento) e **(ii) direção** (o call−put IV spread, o skew de puts OTM, o rácio O/S e a RN-skewness prevêem o *sinal* do retorno do anúncio, com o efeito mais forte documentado a ser >1,5% entre quintis numa janela de 2 dias). O melhor sinal novo e 100% gratuito é o **gap entre o move histórico de anúncios e o implied move atual** (Milian 2023: 14,20%/trimestre no hedge portfolio de straddles, t=2,72).

---

## (a) Tabela por sinal

| # | Sinal | Paper (amostra) | Effect size | Direção | Decaimento | Grátis? (campos yfinance) |
|---|-------|----------------|-------------|---------|------------|---------------------------|
| 1 | **Implied move ATM (precisão)** | Dubinsky-Johannes-Kaeck-Seeger, RFS 2019 (EUA, 2000–2015, firmas líquidas) | Vol. implícita média do dia de anúncio 8,22% vs realizada 7,42% → **sobre-estimação média de 80 pb** (close-to-close; 56 pb close-to-open). Correlação ex-ante↔realizado >50% (perto do máximo dado o erro amostral); correlação transversal com vol. diária pós-anúncio ≈85%. Incerteza média 4–6% em expansão, 10–11% em recessão | Neutra (magnitude) | Evento único | **SIM** — `option_chain(exp).calls/.puts[impliedVolatility, bid, ask, strike]`, 2 expiries |
| 2 | **Gap AvgEA − Implied** (move histórico de 4 anúncios vs implied move) | Milian, JRFM 2023 (2.690 anúncios com weeklies, 2014–2017, mkt cap médio $51,8 mil M) | Hedge Q5−Q1 em straddles = **+14,20%/trimestre (t=2,72)**; Q1 (implied ≫ histórico) = **−5,42%*** ; implied médio 5,72% vs histórico 5,07% (implied excede em 0,65 pp em média; IQR −1,89% a +0,54%). Vol histórica, IV nível e HV−IV **não** prevêem straddle returns nesta amostra | Histórico ≫ implied → comprar straddle; implied ≫ histórico → vender | 1 dia (através do anúncio) | **SIM** — implied move da cadeia + `history()` + `earnings_dates` (retornos abs. de 1 dia dos últimos 4 anúncios) |
| 3 | **Skew de puts OTM** (SKEW = IV put OTM − IV call ATM) | Xing-Zhang-Zhao, JFQA 2010 (1996–2005) | Quintil de skew mais acentuado subdesempenha o mais plano em **10,9%/ano ajustado ao risco**; firmas com skew acentuado têm as piores surpresas de resultados no trimestre seguinte | Skew alto → retorno negativo | Persiste **≥6 meses** (lento) | **SIM** — já implementado (IV a 5% OTM put vs call) |
| 4 | **Call−put IV spread (desvios de put-call parity)** | Cremers-Weinbaum, JFQA 2010 (1996–2005) | Calls relativamente caras vs puts caras: **50 pb/semana**; mais forte com opções líquidas + ação ilíquida; efeito enfraqueceu nos anos finais da amostra | Spread positivo (calls caras) → retorno positivo | Semanal, decai rápido | **SIM** — IV de pares call/put com strike+expiry iguais |
| 5 | **Call−put IV spread NO anúncio** | Atilgan, J. Banking & Finance 2014 | Quintil com calls caras supera quintil com puts caras em **>1,5% na janela de 2 dias do anúncio**; monotónico; spread cresce à medida que o anúncio se aproxima (Lei-Wang-Yan, JBF 2017: IV spread anormal acumulado amplifica a reação, sobretudo com volume de opções elevado) | Puts caras → retorno negativo no anúncio | Concentrado na janela de 2 dias | **SIM** — idem #4, medido em D-1 |
| 6 | **Inovações de IV (ΔIV call, ΔIV put)** | An-Ang-Bali-Cakici, J. Finance 2014 | Sorts em ΔIV de calls: spread Q5−Q1 **≈1%/mês**, persiste até 6 meses; ΔIV de puts prevê retornos negativos | ΔIVcall↑ → positivo; ΔIVput↑ → negativo | Até 6 meses | **PARCIAL** — exige guardar snapshots diários da cadeia (yfinance não dá IV histórica) |
| 7 | **Term structure de IV (slope geral)** | Vasquez, JFQA 2017 | Straddles: decil de slope mais positivo − mais negativo = **27,1%/mês bruto** (14,8% long + 12,2% short); robusto a fatores | Slope ascendente → straddles baratos (comprar) | Mensal | **SIM** — IVs ATM de 2+ expiries |
| 8 | **Extração de event-variance da term structure** (o vosso sinal) | DJKS, RFS 2019, Eq. (4) | σ²ⱼ,term = (σ²ₜ,T₁ − σ²ₜ,T₂)/(T₁⁻¹ − T₂⁻¹). Exemplo validado: AMZN 23-10-2014, IV 8d = 75,28%, 15d = 54,37% → σⱼ = 10,26% (vs 9,87% pelo estimador time-series pós-evento). Correlação com beta histórico ≈60%; dispersão de analistas **não** tem poder incremental | Neutra (magnitude) | Evento | **SIM** — já implementado |
| 9 | **Concavidade da curva de IV (bimodalidade)** | Boloorforoosh et al., Review of Finance 2025 | Curvas de IV côncavas (2.ª derivada de IV vs strike negativa perto do ATM = distribuição risk-neutral bimodal) → straddles delta/vega-neutral **12,98% mais baixos** em dias de anúncio; retornos médios só são negativos na presença de concavidade | Concavidade → não comprar straddle (gamma sobrevalorizado) | Evento | **SIM** — IV vs strike numa única cadeia |
| 10 | **Rácio O/S (volume de opções / volume de ações)** | Johnson-So, JFE 2012 (1996–2010) | Decil baixo − decil alto: **0,34%/semana (19,3% anualizado); 1,47%/mês ajustado ao risco; alfa long-short 1,66%/mês (t=5,54)**. O/S prevê as próprias surpresas de resultados; mais forte com custos de short-selling altos | O/S alto → retorno **negativo** | Semanal→mensal | **SIM** — Σ`volume` da cadeia ×100 / volume de ações |
| 11 | **O/S pré-anúncio → magnitude** | Roll-Schwartz-Subrahmanyam, JFE 2010 | O/S sobe antes de anúncios; O/S pré-anúncio prevê positivamente o **retorno absoluto** pós-anúncio (trading informado) | Magnitude (não direção) | Evento | **SIM** — idem #10 |
| 12 | **Put/Call volume ratio direcional** | Pan-Poteshman, RFS 2006 (dados CBOE de compras de abertura, 1990–2001) | Low P/C − High P/C = **40 pb/dia, ≈1%/semana** — MAS com volume *assinado não-público*; o resultado não é impulsionado por janelas de anúncios. Com dados públicos (Blau-Nguyen-Whitby, JBF 2014): P/C prevê só no horizonte diário e é efémero; O/S domina em semanal/mensal | P/C alto → negativo | Diário, efémero | **PARCIAL** — yfinance só tem volume total não assinado → proxy fraco |
| 13 | **Compras vs vendas de opções antes de eventos agendados** | Weinbaum-Fodor-Muravyev-Cremers, Mgmt Science 2023 | Antes de eventos **agendados** (earnings), só as **vendas** de opções prevêem retornos; as compras só prevêem antes de eventos não-agendados | Vendas informadas | Evento | **NÃO** — exige classificação de trades (dados proprietários) |
| 14 | **RN-skewness (BKM)** | Stilger-Kostakis-Poon, Mgmt Science 2017 (1996–2012) | Long Q5(RNS alta) − short Q1(RNS baixa): **alfa FFC 55 pb/mês (t=2,47)**; impulsionado por ações sobrevalorizadas difíceis de shortar. **Sinal contestado:** Conrad-Dittmar-Ghysels, JF 2013, encontram relação **negativa** (skew mais negativa → retornos maiores) em horizontes mais longos | SKP: RNS baixa → negativo (1 mês) | Mensal | **SIM** — cadeia OTM única (ver fórmula abaixo) |
| 15 | **Pinning / gamma em expirações** | Ni-Pearson-Poteshman, JFE 2005 | Clustering nos strikes altera retornos em **≥16,5 pb** em média no dia de expiração (≈$9 mil M de mkt cap agregado); causado por hedging de market makers | Preço atraído para strikes de OI alto | Dia de expiração | **PARCIAL** — `openInterest` por strike dá "max pain"/walls; o *sentido* do posicionamento dos dealers é um pressuposto não observável (convenção: dealers long calls, short puts); OI da véspera, estático |
| 16 | **Straddle pré-anúncio (comprar D-3, fechar D0)** | Gao-Xing-Zhang, JFQA 2018 (1996–2013) | **+3,34% (altamente significativo)** por evento; maior em small caps, alta volatilidade, alta curtose, surpresas passadas voláteis, opções ilíquidas → o mercado *sub*-estima incerteza nestes segmentos antes do evento | Comprar vol cedo, sair antes do anúncio | Janela D-3→D0 | **SIM** (execução; custos corroem — half-spread médio de straddles weekly = 7,4% em Milian) |
| 17 | **Straddle através do anúncio (prémio de variância de earnings)** | DJKS, RFS 2019 | Straddle ATM aberto antes e fechado no dia seguinte: **média −8%, mediana −10%** (bootstrap significativo) — prémio de salto de earnings robusto. Liu et al. ("Earnings Announcements: Ex-ante Risk Premia"): vender straddles não é lucrativo em média após custos, mas em anúncios de risco acima da mediana rende **0,56%**/evento. Sinclair (Positional Option Trading, 2020) enquadra-o como prémio de risco sistemático colhível — magnitude exata: **NÃO VERIFICADO** | Vender vol através do evento (seletivamente) | Evento | **SIM** (sinal); execução com custos reais |

Nota sobre **call-skew (cauda direita)**: não encontrei literatura robusta que use especificamente o skew de calls OTM como preditor de surpresas positivas em anúncios — **NÃO VERIFICADO**. Os substitutos documentados para a cauda direita são o call−put IV spread (#4, #5), ΔIVcall (#6) e a RN-skewness (#14). Jin-Livnat-Zhang (JAR 2012) confirmam que skews/spreads medidos imediatamente antes de eventos prevêem retornos de curto prazo do evento, mas a *vantagem incremental* dos option traders concentra-se em eventos **não-agendados**; effect sizes exatos do paper: **NÃO VERIFICADO** (acesso bloqueado).

---

## (b) Top-5 sinais a adicionar ao sistema (ranqueados por effect size documentado × implementabilidade grátis)

O sistema já tem: implied move ATM, event-variance por term structure (2 expiries), skew 5%-OTM, rácio P/C. Adicionar, por ordem:

**1. Gap histórico-implícito de earnings (AvgEA − Implied)** — Milian 2023; 14,20%/trimestre, t=2,72; único sinal significativo entre 5 candidatos.
```
AvgEA = média(|retorno close-to-close do dia de reação|) dos últimos 4 anúncios
        → yfinance: tk.earnings_dates (datas) + tk.history() (preços)
Implied = (mid do ATM call + mid do ATM put do expiry imediatamente pós-anúncio) / S
        → tk.option_chain(exp): bid, ask, strike; S de tk.fast_info
Sinal = AvgEA − Implied.  >0 → long straddle; ≪0 (ex.: quintil inferior) → short straddle/evitar compra.
```
**2. Call−put ATM IV spread em D-1 (direcional)** — Cremers-Weinbaum + Atilgan; >1,5% entre quintis na janela de 2 dias; é o preditor *direcional* de anúncio com melhor rácio evidência/custo.
```
CPIV = média ponderada por OI de [IV_call(K,T) − IV_put(K,T)] em pares strike-expiry iguais
     → option_chain: impliedVolatility, openInterest. Tracking diário: o *acumulado* anormal
       nos ~5 dias pré-anúncio reforça o sinal (Lei-Wang-Yan 2017).
CPIV > 0 → inclinação bullish para o anúncio; CPIV < 0 → bearish.
```
**3. Rácio O/S (nível + variação pré-anúncio)** — Johnson-So; 1,47%/mês; sinal negativo direcional + RSS para magnitude.
```
O/S = Σ volume de todos os calls+puts (todas as expiries) × 100 / volume de ações do dia
    → option_chain(exp).calls['volume'] etc. + history()['Volume']
O/S elevado vs média móvel própria → inclinação negativa + move realizado maior.
```
**4. RN-skewness BKM da cadeia única** — Stilger-Kostakis-Poon; 55 pb/mês. Inputs exatos de um snapshot yfinance:
```
Necessário: S (spot), r (taxa sem risco), τ (tempo até expiry), e da cadeia: strikes K,
mid prices de calls OTM (K>S) e puts OTM (K<S) → bid/ask de option_chain.
V = ∫ 2(1−ln(K/S))/K² · C(K)dK  +  ∫ 2(1+ln(S/K))/K² · P(K)dK      (contrato quadrático)
W = ∫ [6ln(K/S)−3ln²(K/S)]/K² · C(K)dK − ∫ [6ln(S/K)+3ln²(S/K)]/K² · P(K)dK   (cúbico)
X = ∫ [12ln²(K/S)−4ln³(K/S)]/K² · C(K)dK + ∫ [12ln²(S/K)+4ln³(S/K)]/K² · P(K)dK (quártico)
μ = e^{rτ}−1 − e^{rτ}V/2 − e^{rτ}W/6 − e^{rτ}X/24
SKEW = (e^{rτ}W − 3μe^{rτ}V + 2μ³) / (e^{rτ}V − μ²)^{3/2}   (integração: regra trapezoidal
sobre os strikes OTM disponíveis; filtrar bid=0)
```
Atenção: usar a expiry pós-anúncio; sinal de curto prazo positivo (SKP), mas literatura com sinais opostos em horizontes longos (CDG 2013) — usar como *tie-breaker*, não como sinal primário.

**5. Concavidade da curva de IV + GEX ingénuo** — Review of Finance 2025 (concavidade → −12,98% em straddles neutros no anúncio) + Ni-Pearson-Poteshman (pinning).
```
Concavidade: ajustar quadrática a IV(ln K/S) nos ±15% ATM; coeficiente de 2.º grau < 0 → bimodal
→ não comprar straddle mesmo com gap histórico-implícito favorável.
GEX ingénuo: Σ [gamma_BS(K,T)·OI_call − gamma_BS(K,T)·OI_put] · 100 · S² · 0,01
(pressuposto padrão dealers long calls/short puts — aproximação, OI da véspera)
+ "max pain"/put-call walls por strike de OI máximo → íman de pinning na expiry da semana do anúncio.
```

---

## (c) Melhor hit rate direcional documentado com sinais de opções isolados

**Declaração explícita:** a literatura académica de topo **não reporta hit rates de classificação direcional** — reporta spreads entre carteiras extremas. Os melhores efeitos direcionais documentados e verificados são: **>1,5% entre quintis extremos na janela de 2 dias do anúncio** (call−put IV spread, Atilgan 2014), **50 pb/semana** (Cremers-Weinbaum), **40 pb/dia** (Pan-Poteshman, mas com volume assinado *não-público* — irreplicável grátis) e **10,9%/ano** (skew, XZZ). Um hit rate direcional explícito (ex.: "57% de acerto") a partir de sinais de opções puros: **NÃO VERIFICADO** — nenhum estudo credível encontrado o reporta; os números de ~55–60% que circulam vêm de modelos ML multi-modais sem features de opções (e nem esses foram verificáveis no abstract). Tradução prática honesta: com quintis a a ±0,75% por evento sobre um move típico de ~5–6%, o edge direcional implícito é modesto — na ordem de poucos pontos percentuais acima de 50% —, e a fração maior do edge documentado em earnings está na dimensão **volatilidade** (magnitude), não na direção.

---

## (d) Fontes

- DJKS, RFS 2019 (PDF): https://research.vu.nl/ws/portalfiles/portal/108247883/Option_Pricing_of_Earnings_Announcement_Risks.pdf · versão 2006: https://business.columbia.edu/sites/default/files-efs/pubfiles/6051/DJ_2006.pdf
- Milian, JRFM 2023 (PDF): https://mdpi-res.com/d_attachment/jrfm/jrfm-16-00270/article_deploy/jrfm-16-00270-v2.pdf · https://www.mdpi.com/1911-8074/16/5/270
- Xing-Zhang-Zhao, JFQA 2010: https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/what-does-the-individual-option-volatility-smirk-tell-us-about-future-equity-returns/ECFD16BA9ACBDC8D577D1BD866FBEA72 · SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1107464
- Cremers-Weinbaum, JFQA 2010: https://www.scirp.org/reference/referencespapers?referenceid=2477593
- Atilgan, JBF 2014: https://www.sciencedirect.com/science/article/abs/pii/S0378426613004081 · https://ideas.repec.org/a/eee/jbfina/v38y2014icp205-215.html
- Lei-Wang-Yan, JBF 2017: https://www.sciencedirect.com/science/article/abs/pii/S0378426617300791
- Jin-Livnat-Zhang, JAR 2012: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-679X.2012.00439.x
- Johnson-So, JFE 2012 (PDF): https://www.travislakejohnson.com/pdfs/Johnson%20So%20OS%202012%20(JFE).pdf
- Roll-Schwartz-Subrahmanyam, JFE 2010: https://ideas.repec.org/a/eee/jfinec/v96y2010i1p1-17.html
- Pan-Poteshman, RFS 2006 (PDF): https://www.mit.edu/~junpan/volume.pdf
- Blau-Nguyen-Whitby, JBF 2014: https://www.sciencedirect.com/science/article/abs/pii/S037842661400106X
- Weinbaum-Fodor-Muravyev-Cremers, Mgmt Sci 2023: https://ideas.repec.org/a/inm/ormnsc/v69y2023i8p4810-4827.html
- Stilger-Kostakis-Poon, Mgmt Sci 2017: https://pubsonline.informs.org/doi/10.1287/mnsc.2015.2379
- Conrad-Dittmar-Ghysels, JF 2013: https://ideas.repec.org/a/bla/jfinan/v68y2013i1p85-124.html
- BKM 2003 estimadores (nota técnica): https://acfr.aut.ac.nz/__data/assets/pdf_file/0008/328931/Pakorn-Bakshi,-Kapadia,-and-Madan-2003-Risk-Neutral-Moment-Estimators.pdf
- An-Ang-Bali-Cakici, JF 2014 (PDF): https://business.columbia.edu/sites/default/files-efs/pubfiles/3954/The%20Joint%20Cross%20Section%20of%20Stocks%20and%20Options.pdf
- Vasquez, JFQA 2017: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1944298 · https://ideas.repec.org/a/cup/jfinqa/v52y2017i06p2727-2754_00.html
- Gao-Xing-Zhang, JFQA 2018 (PDF): https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7B34877AD5E06304BA3C55FBA3219FDD/S0022109018000285a.pdf/anticipating-uncertainty-straddles-around-earnings-announcements.pdf
- Liu et al., "Earnings Announcements: Ex-ante Risk Premia": https://www.aeaweb.org/conference/2024/program/paper/5GGEki7i
- Boloorforoosh et al., Review of Finance 2025 (curvas côncavas): https://academic.oup.com/rof/article/29/4/963/8079062
- Ni-Pearson-Poteshman, JFE 2005: https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577
- ORATS (indústria): https://orats.com/blog/earnings-straddles-strong-season-2026 · https://orats.com/university/volatility-around-earnings
- GEX grátis (indústria): https://gextool.com/ · https://flashalpha.com/tools/gamma-exposure · https://spotgamma.com/gamma-exposure-gex/
- Sinclair, Positional Option Trading: https://www.amazon.com/Positional-Option-Trading-Wiley/dp/1119583519

**Limitações principais:** SSRN e Wiley bloquearam acesso direto a Jin-Livnat-Zhang e Atilgan (effect sizes citados vêm dos abstracts indexados); amostra de Milian é curta (13 trimestres) e só large caps com weeklies; o P/C direcional gratuito (volume não assinado) é um proxy degradado do resultado de Pan-Poteshman; sinais de posicionamento de dealers (GEX) assentam em convenções não observáveis nos dados públicos.


---

# RELATÓRIO B — PRÁTICAS DE FUNDOS (19 pesquisas + 10 fontes profundas)

A investigação está completa — 19 pesquisas web + 10 fontes aprofundadas (incluindo extração local de um PDF do Ernie Chan). Segue o relatório final em português europeu.

---

# O que fazem realmente os fundos event-driven e stat-arb no trading de eventos de resultados
**Investigação quantitativa · 2026-08-05 · Para calibração de um sistema de dados gratuitos (yfinance/EDGAR/web pública)**

---

## (a) O que os profissionais fazem — por fonte, com citações

### 1. Euan Sinclair (Positional Option Trading, Volatility Trading; Hull Tactical/BlueFin)
- No livro *Positional Option Trading* (Wiley, 2020), Sinclair documenta como "edges" válidos: o **prémio de variância**, prémios de estrutura temporal, e **efeitos de earnings**. As estratégias específicas listadas: (i) negociar o **PEAD com vertical spreads**; (ii) negociar **volatilidade através do anúncio**; (iii) **reversão em ações que sobem muito antes de earnings**; (iv) **drift pré-anúncio em empresas que reportam tarde** ("late reporters") ([Robot Wealth — review](https://robotwealth.com/positional-option-trading-by-euan-sinclair-a-review/); [Wiley](https://www.wiley.com/en-us/Positional+Option+Trading:+An+Advanced+Guide-p-9781119583530)).
- Em entrevistas (Outlier Podcast, Flirting with Models, gvol.io), a tese central dele: **o implied move tende a exceder o movimento realizado — não sempre, nem por margem enorme, mas de forma suficientemente consistente para que vender prémio numa grande amostra tenha valor esperado positivo**. O prémio de risco de volatilidade é amplificado à volta de eventos ([Listen Notes — episódios](https://www.listennotes.com/top-podcasts/euan-sinclair/); [gvol.io ep. 8](https://amberdataderivatives.substack.com/p/gvolio-podcast-ep-8-euan-sinclair)).
- **Nota honesta:** os efeitos numéricos exatos (retornos médios por evento, win rates) estão no livro e não são reproduzidos nas reviews/entrevistas públicas que verifiquei — efeitos precisos por estratégia: **NÃO VERIFICADO** em fonte aberta.

### 2. Benn Eifert (QVR Advisors) — vol de eventos
- Na entrevista longa que analisei ([Mutiny Fund](https://mutinyfund.com/benn-eifert-qvr-advisors/)), Eifert descreve a fonte de alpha da QVR como **dislocações estruturais causadas por utilizadores finais de derivados insensíveis ao preço** (hedging institucional, produtos estruturados, fluxo de retalho) — o market maker/fundo é pago por fornecer liquidez e armazenar risco de base. **Não** encontrei declarações públicas dele com números específicos sobre earnings — afirmações específicas de Eifert sobre earnings vol: **NÃO VERIFICADO** ([QVR media](https://www.qvradvisors.com/media)).
- Implicação transferível: o edge dos profissionais de vol de eventos vem de **saber quem é o comprador/vendedor forçado**, não de prever melhor o resultado da empresa.

### 3. AQR — o "earnings announcement premium"
- Frazzini & Lamont (working paper na AQR): comprar todas as ações **que vão anunciar no mês** e vender as que não vão rende **>60 pontos base/mês** (~7–18%/ano), com Sharpe superior a outras anomalias; robusto desde 1927 e forte em large caps ([AQR](https://www.aqr.com/Insights/Research/Working-Paper/The-Earnings-Announcement-Premium-and-Trading-Volume)).
- AQR "Craftsmanship Alpha": gestores com o **mesmo sinal** obtêm resultados materialmente diferentes por decisões de construção — transformação de sinais em pesos, combinação, controlo de risco, trading ([AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Working-Papers/AQR--Craftsmanship-Alpha.pdf)).

### 4. Ernie Chan (QTS Capital) — estratégias documentadas com números
- **PEAD intradiário**: entrar na abertura seguinte ao anúncio, na direção do gap (limiar = 90 dias de desvio-padrão do retorno close→open), sair no fecho do próprio dia. **IR ≈ 1,5 em 2011–2012 (S&P 500), alavancável 4×**; overnight é negativo; o drift encurtou de 1–2 dias para intradiário ([resumo do livro Algorithmic Trading](https://manish13.blogspot.com/2015/08/algorithmic-trading-ernest-chan.html)).
- **Reversão pré-earnings (So & Wang 2014)**: shortar os 18 melhores retornos ajustados ao mercado em t-4→t-2, fechar em t+1: **CAGR 9,1%, Sharpe 1,0** (Russell 3000, 2011-16). Crucial: com datas de earnings *point-in-time* em vez de datas do Yahoo, cai para **CAGR 6,8%, Sharpe 0,8** — o look-ahead nas datas infla resultados ([blog de Chan](http://epchan.blogspot.com/2016/11/pre-earnings-annoucement-strategies.html)).
- **Movimento da data de anúncio (Kramarenko/Deltix)**: se a empresa **antecipou a data** do anúncio (deltaD<0) há menos de 45 dias, comprar no fecho e vender na abertura seguinte: **CAGR 14,95%, Sharpe 2,08** (SPX 2006-15); replicação de Chan: **CAGR 17%, Sharpe 1,9** (Russell 3000 2011-16) (mesma fonte).
- **Kaggle Two Sigma (PDF extraído localmente)**: a estratégia de preços deles teve **Sharpe 1,2 em validação → 0,28 em teste** (overfitting mesmo com logística regularizada); cita o meta-estudo **Beckers 2018 (JPM): IR médio de estratégias de news sentiment < 0,5** (2008-17); conclusão textual: *"Simple technical features do not work. Insights into specific market inefficiencies still required"* ([PDF](https://epchan.com/img/links/What-we-learned-from-Kaggle-Two-Sigma-News-Sentiment-competition.pdf)).

### 5. Academia sobre opções em earnings (o que os desks de vol usam como mapa)
- **Gao, Xing & Zhang (JFQA 2018)**: straddles ATM comprados **3 dias antes** do anúncio e mantidos até ao anúncio rendem **+3,34% por evento** (1996-2013) — o mercado **subavalia** a incerteza, sobretudo em **small caps, baixa cobertura de analistas, alta curtose, surpresas passadas voláteis** ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2204549); [JFQA PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7B34877AD5E06304BA3C55FBA3219FDD/S0022109018000285a.pdf/anticipating-uncertainty-straddles-around-earnings-announcements.pdf)).
- **Replicação recente (BSIC)**: o mesmo trade dá **+1,17% sem custos e -9,07% com custos** — a anomalia foi parcialmente arbitrada e os custos destroem-na para quem paga spreads de retalho ([BSIC](https://bsic.it/straddling-outside-and-into-earnings-part-ii-2/)).
- **Lei, Wang & Yan (JBF 2020)**: o **spread de IV call-put** sobe monotonicamente até ao anúncio e **prevê o retorno do anúncio** — traders informados operam primeiro nas opções ([PDF](https://leiq.bus.umich.edu/papers/Lei_Wang_Yan_JBF_2020.pdf)).
- **Goyal-Saretto (via pesquisa)**: **IV − HV** prevê retornos de straddles a 1 mês; comprar straddles "baratos" vs histórico e vender "caros" gera retornos consistentes ([EFMA paper](http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2017-Athens/papers/EFMA2017_0158_fullpaper.pdf)).

### 6. Market makers de opções: como fixam o implied move e quando erram
- Metodologia tipo ORATS: o implied move é **resolvido a partir da term structure** — separa-se a variância "ambiente" da variância aditiva do evento ("earnings bump"), exigindo que a term structure ex-evento fique racional ([ORATS docs](https://orats.com/docs/core-research); [ORATS guide PDF](http://s3.amazonaws.com/assets.orats.com/ORATS%20Core%20Research%20and%20Data%20Guide%202.0.pdf); [remover efeito de earnings da IV](https://orats.com/blog/how-orats-removes-earnings-effect-from-implied-volatility)).
- Padrões documentados de erro:
  - O implied move **excede** o realizado em **~58% dos eventos** (S&P 500, 5 anos — fornecedor retail) e "~70%" segundo outros fornecedores — números de vendors, não peer-reviewed ([TradeAlgo](https://www.tradealgo.com/trading-guides/options/expected-move-calculator); [OptionsPilot](https://optionspilot.app/blog/options-implied-move-earnings-expected-move)).
  - **Subpreço sistemático** onde faltam olhos: small caps, baixa cobertura, curtose alta (Gao-Xing-Zhang, acima).
  - **Regime muda de sinal**: no Q3 2025, pela primeira vez na série citada, os movimentos realizados excederam os implied em agregado ([TradingRiot](https://blog.tradingriot.com/p/volatility-trading-around-earnings)); e no início de 2026 o straddle médio de earnings rendeu **~+45% em 4 semanas vs média de -2% nos 12 trimestres anteriores** — causas apontadas: maior dispersão entre empresas, sensibilidade ao guidance, macro ([ORATS blog 2026](https://orats.com/blog/earnings-straddles-strong-season-2026)).
  - "First-time reporters"/pós-IPO com implied move sistematicamente errado: **NÃO VERIFICADO** — não encontrei estudo público robusto; o mais próximo é o resultado de Gao et al. sobre baixa cobertura/curtose.
  - Skew: puts a preçar movimentos 30–50% maiores que calls equivalentes (afirmação de vendor — **NÃO VERIFICADO** academicamente) ([OptionsPilot](https://optionspilot.app/blog/options-implied-move-earnings-expected-move)).

### 7. Desks de "earnings drift/momentum" intradiário
- **Zarattini, Barbon & Aziz (SFI WP 24-98)**: ORB de 5 minutos nos **20 "stocks in play"** por volume relativo de abertura (tipicamente movidos por earnings/notícias): **+1.637% total 2016-2023, Sharpe 2,81, alpha anualizado 36%, beta ≈ 0** ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284); [Concretum](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)). Na replicação QuantConnect, o **win rate é ~17%** — o lucro vem da assimetria (stops ATR curtos, corridas longas), não da taxa de acerto ([QuantConnect](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)).
- PEAD clássico multi-semanas: **15%/ano, drawdown -11,2%** (1987-2004, Quantpedia), mas evidência pós-2010 mista/enfraquecida; definição textual das surpresas ainda funcionava 2008-2019; a concorrência de fundos modera a rentabilidade ([Quantpedia](https://quantpedia.com/strategies/post-earnings-announcement-effect); [review ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214635020303750); [mutual funds/competition](https://www.sciencedirect.com/science/article/abs/pii/S037842662030042X)).

### 8. Edge informacional dos desks event-driven (e proxies gratuitos)
- **Expert networks**: chamadas de 30-60 min a 500–1.500 USD/hora (GLG, AlphaSights, Guidepoint, Third Bridge); os fundos "empilham" bibliotecas de transcrições (Tegus/AlphaSense) com chamadas primárias, sob controlo de MNPI ([ExpertNetworks.net](https://expertnetworks.net/expert-networks-for-hedge-funds/)).
- **Alt-data**: cartões de crédito são a categoria nº1 (~18% do gasto), web-scraping ~15%; dois terços dos advisers gastam >1 M USD/ano; scraping de SKUs dá **2-3 semanas de avanço** sobre earnings de retalho ([Kadoa](https://www.kadoa.com/blog/alternative-data-for-hedge-funds); [Young & Calculated](https://youngandcalculated.substack.com/p/alternative-data-inside-hedge-funds); [Crawlbase](https://crawlbase.com/blog/how-hedge-funds-use-web-scraping/)).
- **Proxies com validação académica (todos gratuitos ou quase)**:
  - **Google Trends** do produto principal: prevê surpresas de receita/SUE e o retorno do anúncio; estratégia implementável rende **~2-3% anormais por trimestre**, 2/3 concentrados no anúncio ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0361368223000284); [UCLA Anderson Review](https://anderson-review.ucla.edu/using-google-trends-to-detect-revenue-misreporting/)).
  - **Tráfego web (dados SimilarWeb)**: visitas/pageviews prevêem receita e lucro; **retorno anormal médio de anúncio de 3,4%**; o mercado é lento a incorporar ([The Accounting Review 2025](https://publications.aaahq.org/accounting-review/article/100/6/29/13922/Digital-Traffic-Financial-Performance-and-Stock); [PDF Haas](http://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf); [nota Berkeley](https://newsroom.haas.berkeley.edu/companies-website-traffic-proves-powerful-predictor-of-financial-performance-and-stock-returns/)).
  - **Glassdoor**: melhorias de rating prevêem vendas, rentabilidade e **surpresas do trimestre seguinte** (Green, Huang, Wen & Zhou, JFE 2019) ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3002707); [PDF](https://faculty.georgetown.edu/qw50/EmpReviews.pdf)).
  - **Job postings** (LinkUp e académicos): variações prevêem crescimento de empregados, SG&A, vendas e lucros a 1 ano; caso Booz Allen 2025: colapso de 1.600→700 vagas antes de earnings dececionantes ([LinkUp](https://www.linkup.com/use-cases/predicting-future-earnings-with-alt-data); [Job Board Doctor](https://www.jobboarddoctor.com/2025/09/11/job-postings-as-market-signals/)).
  - **Texto de filings/calls**: "Lazy Prices" — shortar empresas que **mudam o texto** do 10-K/10-Q vs não-mudadores: **até 188 bps/mês de alpha (>22%/ano)**, sem efeito de anúncio (desatenção) ([Journal of Finance 2020](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12885); [NBER w25084](https://www.nber.org/papers/w25084)); o **tom das earnings calls** prevê retornos anormais e domina a própria surpresa nos 60 dias seguintes; LLMs > léxicos ([JBF 2012](https://www.sciencedirect.com/science/article/abs/pii/S0378426611002901); [ICAIF 2023](https://dl.acm.org/doi/fullHtml/10.1145/3604237.3626861)).

### 9. ML em produção para eventos — o que é público
- **Two Sigma/Kaggle "Using News to Predict Stock Movements"** (2018-19): dados de mercado + sentimento Thomson-Reuters 2007-16; soluções vencedoras usaram lags, agregados de mercado inteiro, e ensembles de 2 níveis; sem milagres de accuracy ([Kaggle](https://www.kaggle.com/competitions/two-sigma-financial-news); [entrevista 5º lugar](https://medium.com/kaggle-blog/two-sigma-financial-modeling-code-competition-5th-place-winners-interview-team-best-fitting-279a493c76bd)).
- **WorldQuant "101 Formulaic Alphas"**: todos os alphas publicados são de **preço/volume/VWAP — nenhum é específico de earnings**; a lição é o formato (expressões curtas, cross-sectional, decay rápido) ([arXiv 1601.00991](https://arxiv.org/pdf/1601.00991); [biblioteca de fatores de Stefan Jansen](https://stefan-jansen.github.io/machine-learning-for-trading/24_alpha_factor_library/)).
- **AQR "Can Machines Build Better Stock Portfolios?" / Financial Machine Learning**: o ML institucional rende mais na **construção de carteira e combinação de sinais** do que na previsão pura ([AQR Alternative Thinking 2024-4](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alternative-Thinking-2024-Issue-4-Can-Machines-Build-Better-Stock-Portfolios.PDF); [AQR FML](https://www.aqr.com/Insights/Research/Working-Paper/Financial-Machine-Learning)).

---

## (b) Tabela: vantagens profissionais vs replicabilidade com dados gratuitos

| Vantagem profissional | Replicável grátis? | Como (com dados gratuitos) |
|---|---|---|
| Painéis de cartões de crédito | **NÃO** | Proxy fraco: Google Trends do produto/marca (validado academicamente: 2-3%/trimestre) |
| Web-scraped pricing/SKUs | **PARCIAL** | Scraping próprio de páginas de preços públicas; sem histórico longo nem painel |
| Tráfego web (SimilarWeb pago) | **PARCIAL** | SimilarWeb free tier (top-level, 3 meses); Google Trends como substituto direcional |
| Dados de apps (Sensor Tower) | **PARCIAL** | Ranks públicos das app stores (grátis, diários); downloads/receita estimados são pagos |
| Satélite / geolocalização | **NÃO** | Sem proxy gratuito com validação |
| Expert networks / channel checks | **NÃO** | Proxy ténue: transcrições públicas de calls, Reddit/fóruns setoriais — sem validação robusta |
| Job postings (LinkUp etc.) | **SIM** | Scraping das páginas de carreiras das próprias empresas (é exatamente o que a LinkUp faz); contagens Indeed |
| Sinal Glassdoor | **PARCIAL** | Ratings e contagens visíveis publicamente; deltas trimestrais (JFE 2019 valida o conceito) |
| NLP de filings e calls | **SIM** | EDGAR (diffs de 10-K/Q à "Lazy Prices"), transcrições gratuitas (IR das empresas, Motley Fool) |
| Implied move e sinais de opções | **SIM (com ruído)** | Cadeias de opções do yfinance: implied move ATM, spread IV call-put, IV vs média realizada histórica dos últimos 8-12 eventos |
| Datas de earnings point-in-time + mudanças de data | **SIM** | Registar diariamente o calendário (yfinance/EDGAR 8-K) e construir o histórico próprio; sinal de antecipação de data (Sharpe ~1,9-2,1 documentado) |
| Term-structure solve do "earnings bump" (ORATS) | **PARCIAL** | Aproximável com 2 expirações (curta com evento vs seguinte sem) via yfinance |
| Execução em ms, custos institucionais, borrow | **NÃO** | Mitigar: menos rotação, ordens limitadas, evitar small caps ilíquidas onde o edge bruto é maior mas os custos o comem (BSIC: +1,17% → -9,07%) |
| Breadth de milhares de eventos/trimestre | **PARCIAL** | Automatizar para cobrir centenas de eventos pequenos em vez de poucos grandes |

---

## (c) Hit rates e edges profissionais documentados — benchmark para o nosso sistema

| Estratégia/fundo | Métrica documentada | Fonte |
|---|---|---|
| Renaissance/Medallion (Mercer) | **acerto em 50,75% dos trades** — "podes ganhar milhares de milhões assim" — edge minúsculo × volume enorme | [Quartr](https://quartr.com/insights/edge/renaissance-technologies-and-the-medallion-fund), [Quora/Mercer quote](https://www.quora.com/What-did-Bob-Mercen-mean-when-he-said-that-Renaissance-Technologies-were-100-percent-right-50-75-percent-of-the-time-What-is-their-risk-to-reward-ratio) |
| Merger arb (o "event-driven" com hit rate mais alto) | ~90% dos deals fecham; **+2,0% nos ganhos, -2,8% nas perdas**; Sharpe ~0,9; 7-12% líquido/ano | [Alpha Architect](https://alphaarchitect.com/merger-spread/), [Princeton](https://www.princeton.edu/~markus/teaching/Eco467/08Lecture/08a_Merger_Arbitrage_Intro.pdf) |
| Venda de prémio em earnings | implied > realizado em **~58%** (S&P 500, 5 anos; vendors) a ~70% (afirmação de vendor); perdas de 3-10× o prémio nas caudas | [TradeAlgo](https://www.tradealgo.com/trading-guides/options/expected-move-calculator), [TradingRiot](https://blog.tradingriot.com/p/volatility-trading-around-earnings) |
| Long straddle pré-anúncio (T-3→T) | **+3,34% por evento** (1996-2013) → +1,17% bruto / **-9,07% com custos** hoje | [JFQA](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2204549), [BSIC](https://bsic.it/straddling-outside-and-into-earnings-part-ii-2/) |
| PEAD clássico | 15%/ano (1987-2004); pós-2010 enfraquecido | [Quantpedia](https://quantpedia.com/strategies/post-earnings-announcement-effect) |
| PEAD intradiário (Chan) | IR 1,5 (2011-12) | [epchan](http://epchan.blogspot.com/2016/11/pre-earnings-annoucement-strategies.html) |
| Mudança de data de anúncio | CAGR 15-17%, **Sharpe 1,9-2,1** | [epchan](http://epchan.blogspot.com/2016/11/pre-earnings-annoucement-strategies.html) |
| ORB "stocks in play" | Sharpe 2,81, alpha 36%/ano, **win rate ~17%** (payoffs assimétricos) | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284), [QuantConnect](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/) |
| Earnings announcement premium (AQR) | **~60 bps/mês** | [AQR](https://www.aqr.com/Insights/Research/Working-Paper/The-Earnings-Announcement-Premium-and-Trading-Volume) |
| News sentiment (meta-estudo Beckers 2018 via Chan) | **IR médio < 0,5** | [PDF Chan/Hunter](https://epchan.com/img/links/What-we-learned-from-Kaggle-Two-Sigma-News-Sentiment-competition.pdf) |
| Alt-data académico (Trends/tráfego web) | 2-3%/trimestre; 3,4% no anúncio | ver secção (a).8 |

**Leitura para o nosso sistema:** não há **nenhuma evidência pública** de que fundos profissionais atinjam probabilidades direcionais calibradas >60% por evento de earnings. Os melhores operadores do mundo vivem com 50,75%-58% de acerto; o merger arb chega a ~90% mas com payoff invertido (ganhos pequenos, perdas grandes). O nosso teto de P(≥+5%)≈60% calibrada **não é o problema** — está na zona do que é realisticamente atingível. O nosso **+3,2%/fold no top-3** compara bem com os 60 bps/mês da AQR e os 2-3%/trimestre do alt-data académico, mas cuidado: essas referências são **líquidas de enviesamentos em amostras enormes**; a nossa é uma média por fold em top-3 — o risco é variância e custos, não a média. Onde os profissionais nos batem é em **breadth** (milhares de eventos), **custos** e **construção** — ver (d).5.

---

## (d) As 5 práticas de maior valor adotáveis com dados gratuitos (ordenadas)

1. **Integrar o mercado de opções como prior e como filtro (yfinance chains).** Calcular por evento: implied move ATM; rácio implied/média realizada dos últimos 8-12 eventos; spread IV call-put (Lei-Wang-Yan: prevê a direção do anúncio); term structure curta. Usar o implied move como *prior* da distribuição (é a melhor estimativa agregada disponível) e só atribuir P elevada quando o nosso modelo **e** o sinal de opções concordam. Onde procurar erro do mercado: small caps com pouca cobertura e curtose alta (subpreço — Gao-Xing-Zhang) e nomes com sobrepreço consistente multi-trimestre (TradingRiot).
2. **Datas de earnings point-in-time + sinal de mudança de data.** Guardar snapshots diários do calendário (yfinance/EDGAR): (i) elimina o look-ahead que inflacionou o backtest de So-Wang em +2,3 pp de CAGR; (ii) dá de graça o sinal "empresa antecipou a data" (Sharpe documentado 1,9-2,1) e o drift dos "late reporters" (Sinclair). Custo quase zero, retorno duplo (integridade + alpha).
3. **NLP de EDGAR e transcrições: diffs de 10-K/Q ("Lazy Prices", 188 bps/mês) + tom das calls (prevê o drift de 60 dias).** É a única categoria onde o dado gratuito é **idêntico** ao dos profissionais — o EDGAR é o mesmo para todos; o edge é desatenção, não acesso.
4. **"Revenue surprise score" com proxies gratuitos validados:** Google Trends do produto principal (2-3%/trimestre), contagem de vagas na página de carreiras da empresa, delta de rating Glassdoor, ranks de app stores. Cada um é fraco; a soma z-scored por setor é a versão pobre — mas academicamente validada — do painel de cartões de crédito.
5. **Deslocar o esforço da previsão para a construção: breadth, sizing e custos.** Mercer (50,75%), Grinold (IR = IC × √breadth — [AnalystPrep](https://analystprep.com/study-notes/cfa-level-2/state-and-interpret-the-fundamental-law-of-active-portfolio-management-including-its-component-terms-transfer-coefficient-information-coefficient-breadth-and-active-risk-aggressiveness/)) e a AQR (Craftsmanship) apontam todos no mesmo sentido: parar de tentar subir P(hit) acima de 60% e, em vez disso, (i) cobrir mais eventos por trimestre com apostas menores; (ii) dimensionar por EV/Kelly fracionário e não por convicção; (iii) modelar custos explicitamente (a diferença entre +1,17% e -9,07% no straddle é só custos); (iv) monitorizar regime — o prémio de earnings inverteu o sinal no Q3-2025/2026 (ORATS), portanto qualquer módulo de vol precisa de um interruptor de regime.

---

## (e) Fontes completas

**Sinclair / praticantes:** [robotwealth.com/positional-option-trading-by-euan-sinclair-a-review](https://robotwealth.com/positional-option-trading-by-euan-sinclair-a-review/) · [wiley.com — Positional Option Trading](https://www.wiley.com/en-us/Positional+Option+Trading:+An+Advanced+Guide-p-9781119583530) · [listennotes.com/top-podcasts/euan-sinclair](https://www.listennotes.com/top-podcasts/euan-sinclair/) · [amberdataderivatives.substack.com — gvol.io ep.8](https://amberdataderivatives.substack.com/p/gvolio-podcast-ep-8-euan-sinclair) · [blog.moontower.ai/hard-earned-trading-wisdom](https://blog.moontower.ai/hard-earned-trading-wisdom/) · [mutinyfund.com/benn-eifert-qvr-advisors](https://mutinyfund.com/benn-eifert-qvr-advisors/) · [qvradvisors.com/media](https://www.qvradvisors.com/media)
**Ernie Chan:** [epchan.blogspot.com/2016/11/pre-earnings-annoucement-strategies.html](http://epchan.blogspot.com/2016/11/pre-earnings-annoucement-strategies.html) · [epchan.com — Kaggle Two Sigma PDF](https://epchan.com/img/links/What-we-learned-from-Kaggle-Two-Sigma-News-Sentiment-competition.pdf) · [manish13.blogspot.com — resumo Algorithmic Trading](https://manish13.blogspot.com/2015/08/algorithmic-trading-ernest-chan.html)
**AQR / construção:** [aqr.com — Earnings Announcement Premium](https://www.aqr.com/Insights/Research/Working-Paper/The-Earnings-Announcement-Premium-and-Trading-Volume) · [aqr.com — Craftsmanship Alpha PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Working-Papers/AQR--Craftsmanship-Alpha.pdf) · [aqr.com — Can Machines Build Better Stock Portfolios PDF](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alternative-Thinking-2024-Issue-4-Can-Machines-Build-Better-Stock-Portfolios.PDF) · [aqr.com — Financial Machine Learning](https://www.aqr.com/Insights/Research/Working-Paper/Financial-Machine-Learning) · [analystprep.com — Fundamental Law](https://analystprep.com/study-notes/cfa-level-2/state-and-interpret-the-fundamental-law-of-active-portfolio-management-including-its-component-terms-transfer-coefficient-information-coefficient-breadth-and-active-risk-aggressiveness/)
**Opções/earnings académico:** [ssrn.com/abstract=2204549 — Gao-Xing-Zhang](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2204549) · [cambridge.org — JFQA PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7B34877AD5E06304BA3C55FBA3219FDD/S0022109018000285a.pdf/anticipating-uncertainty-straddles-around-earnings-announcements.pdf) · [bsic.it — Straddling Part II](https://bsic.it/straddling-outside-and-into-earnings-part-ii-2/) · [leiq.bus.umich.edu — Lei-Wang-Yan JBF 2020](https://leiq.bus.umich.edu/papers/Lei_Wang_Yan_JBF_2020.pdf) · [efmaefm.org — IV-HV straddle](http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2017-Athens/papers/EFMA2017_0158_fullpaper.pdf) · [sciencedirect.com — Earnings announcements and option returns](https://www.sciencedirect.com/science/article/abs/pii/S0927539816300743)
**Implied moves / market makers:** [orats.com/docs/core-research](https://orats.com/docs/core-research) · [ORATS Core Research Guide PDF](http://s3.amazonaws.com/assets.orats.com/ORATS%20Core%20Research%20and%20Data%20Guide%202.0.pdf) · [orats.com — remover efeito earnings da IV](https://orats.com/blog/how-orats-removes-earnings-effect-from-implied-volatility) · [orats.com — Earnings Straddles 2026](https://orats.com/blog/earnings-straddles-strong-season-2026) · [blog.tradingriot.com — Volatility Trading Around Earnings](https://blog.tradingriot.com/p/volatility-trading-around-earnings) · [tradealgo.com — Expected Move](https://www.tradealgo.com/trading-guides/options/expected-move-calculator) · [optionspilot.app — implied move earnings](https://optionspilot.app/blog/options-implied-move-earnings-expected-move) · [spotgamma.com — implied earnings moves](https://spotgamma.com/free-tools/implied-earnings-moves/)
**PEAD / intradiário:** [quantpedia.com — Post-Earnings Announcement Effect](https://quantpedia.com/strategies/post-earnings-announcement-effect) · [sciencedirect.com — PEAD review](https://www.sciencedirect.com/science/article/pii/S2214635020303750) · [sciencedirect.com — mutual funds & competition](https://www.sciencedirect.com/science/article/abs/pii/S037842662030042X) · [ssrn.com/abstract=4729284 — Zarattini-Barbon-Aziz](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) · [quantconnect.com — ORB Stocks in Play](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/) · [concretumgroup.com](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)
**Alt-data e proxies gratuitos:** [sciencedirect.com — Google searches & revenue](https://www.sciencedirect.com/science/article/pii/S0361368223000284) · [anderson-review.ucla.edu — Google Trends](https://anderson-review.ucla.edu/using-google-trends-to-detect-revenue-misreporting/) · [publications.aaahq.org — Digital Traffic TAR 2025](https://publications.aaahq.org/accounting-review/article/100/6/29/13922/Digital-Traffic-Financial-Performance-and-Stock) · [faculty.haas.berkeley.edu — PDF](http://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf) · [newsroom.haas.berkeley.edu](https://newsroom.haas.berkeley.edu/companies-website-traffic-proves-powerful-predictor-of-financial-performance-and-stock-returns/) · [ssrn.com/abstract=3002707 — Glassdoor JFE](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3002707) · [linkup.com — predicting earnings](https://www.linkup.com/use-cases/predicting-future-earnings-with-alt-data) · [jobboarddoctor.com — job postings signals](https://www.jobboarddoctor.com/2025/09/11/job-postings-as-market-signals/) · [kadoa.com — alt data guide](https://www.kadoa.com/blog/alternative-data-for-hedge-funds) · [youngandcalculated.substack.com](https://youngandcalculated.substack.com/p/alternative-data-inside-hedge-funds) · [crawlbase.com — hedge funds web scraping](https://crawlbase.com/blog/how-hedge-funds-use-web-scraping/) · [expertnetworks.net — hedge funds guide](https://expertnetworks.net/expert-networks-for-hedge-funds/)
**Texto/NLP:** [onlinelibrary.wiley.com — Lazy Prices JF 2020](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12885) · [nber.org/papers/w25084](https://www.nber.org/papers/w25084) · [sciencedirect.com — call tone JBF](https://www.sciencedirect.com/science/article/abs/pii/S0378426611002901) · [dl.acm.org — PEAD textual ICAIF](https://dl.acm.org/doi/fullHtml/10.1145/3604237.3626861)
**ML/quant:** [kaggle.com/competitions/two-sigma-financial-news](https://www.kaggle.com/competitions/two-sigma-financial-news) · [medium.com — 5th place interview](https://medium.com/kaggle-blog/two-sigma-financial-modeling-code-competition-5th-place-winners-interview-team-best-fitting-279a493c76bd) · [arxiv.org/pdf/1601.00991 — 101 Formulaic Alphas](https://arxiv.org/pdf/1601.00991) · [stefan-jansen.github.io — alpha factor library](https://stefan-jansen.github.io/machine-learning-for-trading/24_alpha_factor_library/)
**Hit rates:** [quartr.com — Renaissance/Medallion](https://quartr.com/insights/edge/renaissance-technologies-and-the-medallion-fund) · [quora.com — citação de Mercer](https://www.quora.com/What-did-Bob-Mercen-mean-when-he-said-that-Renaissance-Technologies-were-100-percent-right-50-75-percent-of-the-time-What-is-their-risk-to-reward-ratio) · [alphaarchitect.com — merger arb](https://alphaarchitect.com/merger-spread/) · [princeton.edu — merger arb lecture](https://www.princeton.edu/~markus/teaching/Eco467/08Lecture/08a_Merger_Arbitrage_Intro.pdf)

**Itens NÃO VERIFICADO:** efeitos numéricos exatos por estratégia nos livros de Sinclair (existem no livro, não em fonte aberta); afirmações específicas de Eifert sobre earnings vol; mispricing sistemático em "first-time reporters"/pós-IPO; o "70% do tempo" e o skew put/call de 30-50% (números de vendors retail, sem peer review).

**Conclusão-chave para o sistema:** o teto de ~60% de P(≥+5%) calibrada não é uma deficiência — nenhuma fonte pública mostra profissionais acima disso em direção pós-earnings. O que os separa é breadth, custos, sizing e o uso do mercado de opções como prior. As cinco práticas do ponto (d) são o caminho de maior EV com dados gratuitos.


---

# RELATÓRIO D — ALT-DATA E NLP (15 pesquisas + 5 PDFs lidos)

A investigação está completa (15 pesquisas web + leitura direta de 5 papers em PDF). Segue o relatório final em português europeu.

---

# Alt-data e NLP com poder preditivo DOCUMENTADO para surpresas de resultados — só o que é replicável GRÁTIS (agosto 2026)

**Nota metodológica:** distingo sempre entre sinais que **preveem a surpresa antes do anúncio** (utilizáveis) e sinais que apenas **reagem ao anúncio** (inúteis para o vosso caso). Efeitos citados foram extraídos diretamente dos papers (li os PDFs originais de 5 deles). Tudo o que não consegui confirmar está marcado **NÃO VERIFICADO**.

## (a) Tabela por fonte

| Fonte | O que prevê (pré-evento?) | Efeito documentado | Estudo | GRÁTIS 2026 | Rota de implementação |
|---|---|---|---|---|---|
| **Tráfego web (SimilarWeb)** | Surpresas de receita vs consenso E vs random walk sazonal; SIM, pré-evento (sinal acumula durante o trimestre) | Hedge portfolio Δtráfego (quartil topo−fundo): **41–94 bps/mês** de alfa (FF5+momentum+liquidez+inv.+profit.); concentrado em firmas com sites transacionais e baixa propriedade institucional; amostra 1.067 firmas, 2017–2020 | Armstrong, Konchitchki & Zhang, *The Accounting Review* 100(6), nov. 2025, DOI 10.2308/TAR-2023-0133 — PDF: http://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf | **NÃO** (SimilarWeb: sem free tier real em 2026 — trial de 7 dias, 15 ações/dia; API só paga) | Proxies grátis: Cloudflare Radar API (rank exato só top-100, depois buckets) e Tranco top-1M diário. **Honestidade: rank ≠ visitas; o efeito documentado usa Δvisitas — o proxy grátis é fraco e não valida o efeito** |
| **Google Trends (SVI de produtos)** | Surpresas de receita (SUS), SUE, SAFE e retorno na janela de anúncio; SIM, pré-evento | +1 DP em ΔSVI → **+0,20 DP na surpresa de receita** (t=9,86); ajustado a sazonalidade: coef. 0,487 (t=5,17), 0,116 com controlo de lag (t=2,43); SAFE só significativo em alta dispersão de analistas; **CAR 3 dias: ~20 bps por 1 DP (t=2,64), ~17% anualizado**, robusto a controlar a própria surpresa | Da, Engelberg & Gao, "In Search of Earnings Predictability" (working paper 2010): https://care-mendoza.nd.edu/assets/152190/engelberg.pdf ; sucessor publicado: https://www.sciencedirect.com/science/article/pii/S0361368223000284 | **SIM, mas frágil** — pytrends **MORTO** (arquivado abr. 2025, 429 sistemáticos); sucessor mantido: `trendspy`; API oficial Google em alpha fechada (candidatura) | `trendspy` + termos de produto (não ticker), Δ log trimestral do SVI do produto principal; throttling agressivo e cache obrigatória |
| **App data (downloads)** | Earnings do trimestre seguinte + erros de previsão dos analistas; SIM, pré-evento | L/S em downloads anormais: **12% EW / 11% VW anualizado**; downloads preveem fortemente os resultados do trimestre seguinte | Chen, Liu & Wu (SSRN 2024): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4851807 | **PARCIAL** — dados de downloads (Sensor Tower/data.ai/Apptopia) são pagos; claim da Apptopia ("leading indicator >70% das vezes") é **marketing, não académico** | Grátis: Apple RSS Marketing Tools v2 (https://rss.marketingtools.apple.com/, top-100 por país, só rank); velocidade de `userRatingCount` via iTunes Lookup API como proxy de downloads — **rota prática sem validação académica, NÃO VERIFICADO** |
| **Job postings** | Crescimento a 1 ano de vendas, empregados, SG&A e earnings; SIM mas horizonte lento (anual, não trimestral) | Associação positiva documentada com crescimento futuro de vendas/earnings (números exatos não extraídos por mim — não cito o que não li) | Gutierrez, Lourie, Nekrasov & Shevlin, "Are Online Job Postings Informative to Investors?", *Management Science*: https://merage.uci.edu/news/2020/12/How-Online-Job-Posting-Data-Could-Change-the-Game-for-Investors.html ; LinkUp (pago): https://www.linkup.com/use-cases/the-market-reaction-to-job-listing-data | **SIM** (via ATS) — LinkUp/Indeed pagos ou bloqueados | **APIs públicas sem autenticação**: `boards-api.greenhouse.io/v1/boards/{empresa}/jobs` e `api.lever.co/v0/postings/{empresa}?mode=json` — contagem diária por empresa/departamento. Cobertura enviesada para tech/mid-cap |
| **Glassdoor (ΔRating)** | Surpresas de anúncio **um trimestre à frente** (erros de consenso + CAR 3 dias) e retornos; SIM, pré-evento | VW quintil topo−fundo de ΔRating trimestral: **+0,74%/mês no trimestre seguinte**; drivers: subratings *Career Opportunities* e *Senior Management*; mais forte com reviews de empregados atuais e da sede; 3.906 firmas, 2008–2016 | Green, Huang, Wen & Zhou, *JFE* 2019: https://faculty.georgetown.edu/qw50/EmpReviews.pdf ; https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300662 | **CINZENTO** — sem API; Cloudflare + login wall, mas endpoints internos `/bff/` devolvem JSON de reviews sem login (curl_cffi): https://alterlab.io/blog/how-to-scrape-glassdoor-complete-guide-for-2026 | Scraping mensal do rating médio por empresa (mín. 15 reviews/trimestre como no paper); risco ToS |
| **Reviews de consumidores** | Amazon: ratings anormais → surpresas de receita e earnings; SIM. Yelp: receita de **independentes**, NÃO de cadeias | Amazon (Huang, *JFE* 2018): L/S ratings anormais **55,7–73,0 bps/mês**, sem reversão; Yelp (Luca, HBS): +1 estrela → +5–9% receita **mas efeito nulo em cadeias** — mau proxy de SSS de cotadas | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2758807 ; https://www.hbs.edu/faculty/Pages/item.aspx?num=41233 | **NÃO** — Yelp Fusion acabou com o free tier (trial 5.000 calls/30 dias): https://business.yelp.com/data/resources/pricing/ ; Google Places API devolve **máx. 5 reviews por local**; scraping Amazon à escala viola ToS | Sem rota grátis séria; fechar |
| **NLP: call anterior → próxima surpresa** | **Direção da surpresa de EPS do trimestre seguinte (~3 meses antes)** — exatamente o vosso caso | Hierarchical FinBERT: **76,56% acc.** vs AR(1) 58,33% e LM+logístico 60,20% (binário balanceado, surpresas materiais); BOW+GBDT 71,43% — quase todo o ganho com modelos leves; dataset (MSCI USA 2004–2011, 5.168 calls) e código **libertados** | Koval, Andrews & Yan, *Findings of ACL 2023*: https://aclanthology.org/2023.findings-acl.520.pdf ; código: https://github.com/rosskoval/fc-es-ccts | **SIM** — FinBERT corre localmente; transcripts: Motley Fool (scraping viável mas bloqueia IPs datacenter), Seeking Alpha (limitado), PDFs de IR | Pipeline: transcript da call do trimestre t → FinBERT hierárquico (ou GBDT sobre n-gramas, 71%!) → probabilidade de beat/miss em t+1 |
| **NLP: Δtom QoQ (delta Loughran-McDonald)** | Earnings futuros e incerteza; analistas sub-reagem → drift; SIM, pré-evento | "Bleak tone changes" (subida de negatividade vs trimestre anterior, controlando press release e perguntas) preveem earnings mais baixos; estratégia calendário: **~0,3%/mês risk-adjusted**; 100.000 calls 2003–2016; assimétrico (negativo forte, positivo fraco) | Druz, Petzev, Wagner & Zeckhauser, *Financial Analysts Journal* 2020: https://www.hks.harvard.edu/sites/default/files/HKSEE/HKSEE%20PDFs/DruzPetzevWagnerZeckhauser_Tone_2020.pdf | **SIM** — dicionário LM é gratuito; mesma infra de transcripts do ponto anterior | Δ(% palavras negativas LM) na secção de apresentação, QoQ; sinal só nos "upticks" de negatividade |
| **NLP: mudanças textuais 10-K/10-Q (EDGAR)** | Earnings futuros, profitabilidade, más notícias, falências; **sem efeito no dia da publicação** — retornos acumulam depois → utilizável pré-anúncio seguinte | Short "changers"/long "non-changers": **até 188 bps/mês de alfa** (>22%/ano); sinal nas secções MD&A, fatores de risco, litígios, menções a CEO/CFO; ~354.000 filings 1995–2014 | Cohen, Malloy & Nguyen, "Lazy Prices", *Journal of Finance* 2020: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12885 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1658471 | **SIM, 100%** — já têm EDGAR | Similaridade (cosseno/Jaccard) entre 10-Q/10-K consecutivos da mesma firma; sinal = queda de similaridade |
| **Expectations management (walk-down)** | Surpresas positivas "fabricadas" e retorno no mês do anúncio; SIM, ex-ante | Firmas com alto incentivo a gerir expectativas (proxy EMI: cobertura de analistas, prop. institucional, crescimento de vendas, Altman Z) rendem **+64 bps EW (t=4,03) / +80 bps VW (t=3,49) no mês de anúncio** e retornos baixos antes; ~320.000 anúncios 1985–2015 | Johnson, Kim & So, "Expectations Management and Stock Returns": https://www.travislakejohnson.com/JohnsonKimSo.pdf | **SIM, 100%** — todos os inputs saem do yfinance/EDGAR que já têm | Compósito PCA dos 4 proxies; nota: no Da-Engelberg-Gao, o nº de guidances positivas/negativas emitidas também prevê a surpresa com o sinal esperado (8-K item 2.02/7.01) |
| **Estimize (estimativas crowdsourced)** | Diretamente a surpresa: gap Estimize-vs-Wall Street antes do anúncio → excess returns | Consenso Estimize mais preciso que o da Street **65% das vezes com 20+ contribuidores** (claim do vendor apoiado em estudo da Deutsche Bank); valor incremental confirmado academicamente (Jame et al.) | Jame, Johnston, Markov & Wolfe, "The Value of Crowdsourced Earnings Forecasts": https://www.researchgate.net/publication/296706882_The_Value_of_Crowdsourced_Earnings_Forecasts ; https://www.estimize.com | **SIM se contribuírem** — modelo contribute-to-access (submeter estimativa → ver as dos pares); site ativo em 2026 (páginas FQ2-2026 live); feed completo é pago (FactSet) | Submeter estimativas próprias e ler o consenso crowd vs consenso oficial por ticker |
| **Satélite/geolocalização** | — | Estudos existem (parking lots → SSS) mas SÓ com imagens comerciais ~50 cm; Sentinel-2 (10 m) e Landsat (15–30 m) **não resolvem carros** | https://www.sciencedirect.com/science/article/abs/pii/S0022435922000240 ; https://skyfi.com/en/blog/high-resolution-satellite-imagery | **NÃO — confirmado e fechado** | Nenhuma |
| **Social além do Reddit** | — | X: pago. StockTwits: **novos registos de API suspensos** ("em revisão", sem aceitar registos — efetivamente morto para novos utilizadores): https://api.stocktwits.com/developers . Bluesky: firehose gratuito mas **zero testes preditivos documentados para surpresas** (NÃO VERIFICADO). GDELT: grátis e com estudos, mas ao nível de índice/vol/macro, não surpresas firm-level | — | Bluesky/GDELT grátis, sem evidência para o vosso alvo | Não priorizar |

## (b) Top-5 por (efeito documentado × exequibilidade grátis)

1. **NLP na call do trimestre anterior → direção da próxima surpresa** (Koval et al., ACL 2023). Efeito grande (76,6% vs 58,3% do baseline temporal, horizonte de 3 meses — é *prever*, não reagir), código e dataset públicos, FinBERT local. Nota chave: **BOW+GBDT dá 71,4%** — não precisam de GPU para capturar a maior parte do sinal.
2. **"Lazy Prices" sobre EDGAR** (JF 2020). Até 188 bps/mês documentado em journal de topo, implementação trivial (similaridade entre filings consecutivos), custo zero, e vocês já ingerem EDGAR. O retorno acumula *depois* da publicação do filing → posicionamento antes do anúncio seguinte.
3. **EMI / expectations management** (Johnson-Kim-So). +64–80 bps no mês do anúncio, todos os inputs já existem no vosso stack; prevê a direção da surpresa "fabricada" pelo walk-down. Complemento natural: contar guidances positivas/negativas nos 8-K entre trimestres.
4. **Δtom QoQ nas calls** (Druz et al., FAJ 2020). ~0,3%/mês; partilha 100% da infraestrutura de transcripts com o nº 1; capturar sobretudo *subidas* de negatividade.
5. **Google Trends via `trendspy`** (Da-Engelberg-Gao). ~20 bps/anúncio por 1 DP e previsão de surpresa de receita; grátis mas operacionalmente frágil (pytrends morto; rate limits) — usar termos de produto, não tickers, e só em firmas com alta dispersão de analistas (é onde o efeito vive).

*Menções honrosas:* contagens Greenhouse/Lever (grátis, limpo, mas horizonte anual e cobertura enviesada); Glassdoor ΔRating (efeito forte mas acesso cinzento); Estimize (prevê diretamente a surpresa, grátis se contribuírem).

## (c) Secção honesta: o que NÃO é replicável grátis (o teto)

Os edges famosos dos fundos de alt-data **não têm proxy gratuito fiel** — é importante saberem que o teto de ~60% de confiança calibrada não será quebrado por aqui:
- **Painéis de cartões de crédito/débito** (Second Measure/Bloomberg, M Science, Yodlee): o melhor preditor conhecido de surpresas de receita consumer; impossível grátis, sem sucedâneo.
- **Satélite e geolocalização** (RS Metrics, Orbital Insight, Placer.ai, SafeGraph): resolução gratuita é 20–60× insuficiente; foot traffic de telemóveis nunca foi gratuito.
- **Tráfego web real** (SimilarWeb): o paper de 2025 é dos mais fortes que existem (41–94 bps/mês), mas o efeito usa *visitas medidas por painel*; Tranco/Cloudflare Radar dão *ranks* com granularidade grosseira — dá para detetar colapsos/explosões, não o Δ fino que gera o alfa.
- **Downloads/DAU exatos de apps** (data.ai, Sensor Tower, Apptopia): o RSS da Apple dá rank top-100, não volumes; o proxy de contagem de ratings é engenhoso mas não validado.
- **Email receipts** (Edison, Measurable AI): sem equivalente.

O que É replicável grátis, com evidência de journal de topo, é quase todo **texto**: EDGAR (Lazy Prices, EMI, guidance) e transcripts de calls (direção da próxima surpresa, Δtom). É aí que está o vosso ROI.

## (d) URLs adicionais usados

- pytrends morto / sucessores: https://apiserpent.com/blog/pytrends-dead-google-trends-data-2026 ; https://meetglimpse.com/software-guides/pytrends-alternatives/
- Cloudflare Radar rankings: https://blog.cloudflare.com/radar-domain-rankings/ ; https://developers.cloudflare.com/api/resources/radar/subresources/ranking/methods/top/ ; Tranco: https://tranco-list.eu/
- SimilarWeb pricing 2026: https://www.saaspricepulse.com/tools/similarweb
- Haas newsroom (resumo do paper de tráfego): https://newsroom.haas.berkeley.edu/companies-website-traffic-proves-powerful-predictor-of-financial-performance-and-stock-returns/
- Scraping Motley Fool: https://apify.com/jungle_synthesizer/motley-fool-earnings-transcripts-scraper ; guia geral: https://stefan-jansen.github.io/machine-learning-for-trading/03_alternative_data/02_earnings_calls/
- Benchmark recente FinCall-Surprise (2.688 calls 2019–21, open-source; alerta: accuracies altas enganam por desbalanceamento de classes e LLMs ainda falham no áudio): https://arxiv.org/abs/2510.03965
- ATS scraping 2026: https://dataresearchtools.com/how-to-scrape-lever-and-greenhouse-job-boards-programmatically-2026/
- Yelp/Google reviews limites: https://appdevelopermagazine.com/yelp-fusion-api-outrageous-new-pricing/ ; https://issuetracker.google.com/issues/35825957
- Exemplo de "reação, não previsão" (para o vosso critério 9): https://github.com/rj694/earnings-sentiment — FinBERT sobre a call do próprio anúncio dá ρ≈0,3 a 1 dia que desaparece em 5 dias; é reação, não é utilizável pré-evento.

**Avisos finais de integridade:** (i) o paper Da-Engelberg-Gao citado é um working paper de 2010 — nunca confirmei publicação em journal dessa versão específica; (ii) não extraí os coeficientes exatos do paper de job postings (li apenas fontes secundárias); (iii) os 65% do Estimize e os "70%" da Apptopia são claims de vendor (o primeiro tem apoio académico via Jame et al., o segundo não — NÃO VERIFICADO); (iv) o proxy iTunes `userRatingCount` é uma rota prática minha, sem paper que a valide.


---

# RELATÓRIO A — ACADEMIA (26 pesquisas + 3 papers lidos página a página)

A investigação está completa — 26 pesquisas e leitura direta de 3 papers (Loughran-McDonald, Johnson-So, Gu-Kelly-Xiu) para extrair tabelas exatas. Segue o relatório final em pt-PT.

---

# EVIDÊNCIA ACADÉMICA PARA PREVISÃO DA REAÇÃO A ANÚNCIOS DE RESULTADOS (HORIZONTE 1–2 DIAS)
**Revisão de literatura quantitativa — 2026-08-05**

## Sumário executivo

1. **O teto é baixo e está documentado**: o R² out-of-sample mensal ao nível da ação é 0,26–0,40% (Gu-Kelly-Xiu, lido diretamente da Tabela 1 do paper RFS 2020). Na janela do anúncio, as regressões académicas de CAR(-1,+1) sobre sinais pré-anúncio têm R² ajustado de ~1% (Johnson-So, Tabela 7, lida diretamente). A vossa confiança calibrada que nunca passa ~60% é consistente com a literatura, não é um defeito do sistema.
2. **A família de preditores com melhor evidência direta para a janela do anúncio são as opções** (skew, volatility spread, O/S, variação de IV) — mas Muravyev-Pearson-Pollet (2022) mostram que ~2/3 dessa previsibilidade é fee de empréstimo de ações (short-sale constraints), não alfa colhível.
3. **PEAD e o prémio de anúncio morreram nos EUA em large caps**: Martineau (CFR 2022) — PEAD inexistente em large caps desde 2006; Heitz-Narayanamoorthy-Zekhnini — prémio de anúncio desapareceu nos EUA pós-2004 (migrou para janelas de 8-K); Christensen-Timmermann-Veliyev (2026) — formação de preços eficiente pós-2016, com a reação em saltos no after-hours.
4. **Atenção retail prevê direção — mas ao contrário do intuitivo**: atenção alta → pressão compradora → pop → **reversão** (Da-Engelberg-Gao: +30 pb em 2 semanas, revertido no ano; Barber et al. 2022: -4,7% em 20 dias nos top de herding do Robinhood).
5. **Decay pós-publicação é a regra**: -26% out-of-sample, -58% pós-publicação (McLean-Pontiff); 65% de 452 anomalias falham t>1,96 com value-weighting (Hou-Xue-Zhang).

---

## 1. Tabelas por preditor (efeito, sobrevivência, viabilidade com dados gratuitos)

### 1.1 Machine learning cross-seccional (Gu-Kelly-Xiu e sucessores)

Números lidos diretamente do PDF publicado (RFS 2020, Tabela 1; amostra 1957–2016, teste OOS 1987–2016; 94 características + 74 dummies SIC + 8 macro = 920 covariáveis):

| Modelo | R²oos mensal (todas as ações) | R²oos mensal (top-1000 por mcap) |
|---|---|---|
| OLS (920 features) | **-3,46%** | -11,28% |
| OLS-3 (size, value, momentum) | 0,16% | 0,31% |
| PLS / PCR | 0,27% / 0,26% | -0,14% / 0,06% |
| Elastic Net / GLM | 0,11% / 0,19% | 0,25% / 0,14% |
| Random Forest / GBRT | 0,33% / 0,34% | 0,63% / 0,52% |
| NN1–NN5 | 0,33–0,40% (**pico NN3 = 0,40%**) | 0,49–**0,70%** |

- Horizonte anual: R²oos ~2,5–3,6% (NN3 3,40%). Redes com >3 camadas **não** melhoram.
- **Features dominantes** (Figuras 4–5, lidas do paper): tendências de preço — reversão de curto prazo (mom1m), momentum 12m, variação de momentum, momentum industrial, maxret; liquidez — market cap (mvel1), dollar volume, turnover, bid-ask spread; volatilidade — retvol, idiovol. Variáveis contabilísticas têm importância baixa ao horizonte mensal.
- **Sucessores/restrições económicas** — Avramov-Cheng-Metzker (Management Science 2023): excluir microcaps corta os lucros ML em **64%**; excluir sem rating **52%**; excluir distressed **77%**; custos de transação degradam mais (turnover alto). Chen-Lopez-Lira-Zimmermann (arXiv 2212.10317): decay médio de ~42% fora de amostra nos preditores publicados.
- **Viabilidade dados gratuitos**: SIM — as features dominantes (preço/volume) vêm todas de yfinance; contabilísticas de EDGAR. Nota: o vosso feature set (distância ao máximo 52s, RSI, momentum, volume relativo, log mcap) já cobre o essencial do que o GKX identifica como dominante.

### 1.2 Preditores de opções pré-anúncio

| Preditor | Paper | Amostra | Efeito documentado | Sobrevive pós-publicação? | Dados gratuitos? |
|---|---|---|---|---|---|
| IV smirk (put OTM − call ATM) | Xing-Zhang-Zhao, JFQA 2010 | ≈1996–2005 (OptionMetrics) | Quintil smirk mais acentuado subdesempenha o menos acentuado em **10,9%/ano** ajustado ao risco; persiste ~6 meses; smirks acentuados → piores choques de earnings no trimestre seguinte | PARCIAL — Muravyev-Pearson-Pollet: ~2/3 do sinal é borrow fee; excluir ações high-fee elimina fração semelhante | **PARCIAL** — yfinance dá chains com IV ao vivo (sinal calculável hoje para o screening), mas **não há histórico grátis** para backtest; exige auto-arquivo diário |
| Volatility spread (IV call − IV put, mesmo strike) | Cremers-Weinbaum, JFQA 2010 | 1996–2005 | Calls relativamente caras vs puts caras: **50 pb/semana** de hedge return | PARCIAL — mesma crítica MPP (2/3 = borrow fees) | **PARCIAL** (idem: live sim, histórico não) |
| Skew/spread imediatamente antes de eventos | Jin-Livnat-Zhang, JAR 2012 | eventos c/ EAs | Medidas de opções **imediatamente antes** do evento têm maior poder preditivo para o retorno do evento do que em janelas afastadas ou pseudo-eventos; para EAs (agendados) o efeito existe mas é mais forte em eventos não agendados. Magnitudes exatas: NÃO VERIFICADO (não extraí as tabelas) | Parcialmente — lógica confirmada por literatura posterior (JBF 2017: build-up monotónico do spread até ao EA, preditivo sobretudo com volume de opções elevado) | **PARCIAL** |
| ΔIV de calls / puts (1 mês) | An-Ang-Bali-Cakici, JF 2014 | ≈1996–2011 (fim NÃO VERIFICADO) | Q5−Q1 de subidas de IV de calls: **~1%/mês** nos retornos seguintes; subidas de IV de puts → retornos negativos; persiste ~6 meses | NÃO VERIFICADO em amostras pós-2015 | **PARCIAL** — precisa de série diária de IV (auto-arquivo) |
| O/S ratio (volume opções/ações) | Roll-Schwartz-Subrahmanyam JFE 2010; **Johnson-So JFE 2012** | 1996–2010; **44.669 EAs** | Geral: D1−D10 = **0,34%/semana (19,3% anualizado)**, decai após semana 1, insignificante após semana 6. **Teste EA (Tabela 7, lida do paper)**: por decil de O/S da semana anterior — SURPRISE -0,004 (t=-2,36), SUE -0,008 (t=-2,06), **CAR(-1,+1) -0,041%/decil (t=-2,11)** ⇒ spread D1-D10 ≈ **-0,37% na janela de 3 dias**; adj-R² da regressão de CAR = **1,06%**. Pós-anúncio (CAR+2,+5): insignificante | Sinal mais forte com short-sale costs altos (i.e., outra vez fricções); RSS: O/S pré-EA prevê |retorno| pós-EA | **PARCIAL** — volume de opções agregável do chain do yfinance (snapshot diário, auto-arquivo) |
| Volume anormal de calls OTM pré-evento | Augustin-Brenner-Subrahmanyam (M&A); análogos para EAs | tomadas de controlo | Volume anormal de opções é a única medida que prevê robustamente o retorno do anúncio (contexto M&A); em EAs a evidência é via build-up de spreads + volume | Evidência EA-específica mais fraca; NÃO VERIFICADO magnitude EA | **PARCIAL** |
| Preço do straddle ATM pré-EA (implied move) | Gao-Xing-Zhang, JFQA 2018 | pré-2018 | Comprar straddle ATM 3 dias antes até ao dia do EA rende **+3,34%** (mercado subestima a incerteza do EA); maior em small caps, alta vol, earnings historicamente voláteis, ilíquidas | NÃO VERIFICADO pós-publicação | **PARCIAL live** — o implied move de hoje é grátis no yfinance; é sinal de **magnitude**, não de direção: diretamente útil para os vossos intervalos conformal/quantile loss |
| A explicação incómoda | **Muravyev-Pearson-Pollet, 2022** (lido do PDF) | c/ dados Markit | Spread e skew de IV refletem mecanicamente o **stock borrow fee** omitido no cálculo da IV; previsibilidade cai **~2/3** ajustando aos fees; idem excluindo ações high-fee | — | Borrow fees não são gratuitos; proxy parcial: short interest (FINRA, quinzenal, grátis) |

### 1.3 Refinamentos de SUE e prémios de anúncio

| Preditor | Paper | Efeito | Estado em 2026 | Grátis? |
|---|---|---|---|---|
| Revenue SUE (SURGE) | Jegadeesh-Livnat, JAE 2006 + FAJ | Reação no dia do anúncio relacionada com surpresas de receitas contemporâneas **e passadas**; drift pós-EA significativo para grandes surpresas de receitas **controlando por SUE**; drift mais forte quando receita e EPS surpreendem na mesma direção. Magnitudes exatas: NÃO VERIFICADO | Sujeito ao mesmo colapso do PEAD (Martineau); componente "surpresa de receita passada → reação seguinte" é ex-ante e distinto do vosso sandbagging de EPS | **SIM** (série temporal de receitas via EDGAR/yfinance; vs consenso de analistas: PARCIAL) |
| Momentum de revisões de analistas | Zhang et al. (UCLA/anderson); lit. de drift | Revisões agregadas são melhor sinal do que SUE para retornos pós-EA; retornos máximos quando SUE no decil mínimo mas revisões no decil máximo; responsividade dos analistas desloca a reação para a janela do evento | Qualitativamente vivo; magnitudes recentes NÃO VERIFICADO | **PARCIAL** — yfinance expõe contagens de revisões up/down 30d correntes, mas sem histórico point-in-time grátis |
| Earnings announcement premium | Frazzini-Lamont, NBER 2007 | Prémio **>7%/ano**; estratégia mensal 7–18% anualizado; explicação por atenção (compra retail previsível) | **Desapareceu nos EUA pós-2004** (Heitz-Narayanamoorthy-Zekhnini): migrou para janelas de 8-K com a regulação de disclosure de 2004; permanece internacional (UK: 88 pb na semana do EA) | **SIM** (datas de EA são grátis) — mas o efeito US morreu |
| Prémio de risco do dia de anúncio | Savor-Wilson, JF 2016 | Anunciantes ganham **~9,9% anualizado** anormal; covariância com cash-flow news do mercado dispara em dias de EA (é risco sistemático, não mispricing) | Mesma erosão pós-2004 nos EUA (ver acima) | **SIM** |
| PEAD clássico | Bernard-Thomas → Martineau CFR 2022 | Hedge trimestral ~5–6% (anos 70–80) → ~4% (2000s) → **2–3% ou menos (2010s)** → **zero em large caps desde 2006**; preços refletem a surpresa no próprio dia | **Morto onde é tradeable** | SIM (mas inútil) |

### 1.4 Atenção e retail

| Preditor | Paper | Efeito (com DIREÇÃO) | Grátis? |
|---|---|---|---|
| SVI Google (ASVI) | Da-Engelberg-Gao, JF 2011 (Russell 3000, ≈2004–2008) | ASVI elevado → **+30 pb** ajustado a características nas 2 semanas seguintes → **reversão quase completa dentro do ano**. Mecanismo: atenção retail → pressão compradora. SVI de produtos prevê surpresas de receitas/earnings e retornos de anúncio | **SIM** — Google Trends (com ruído de amostragem; usar médias de múltiplos downloads) |
| Atenção → compra | Barber-Odean, RFS 2008 | Retail é comprador líquido de ações "attention-grabbing" (notícias, volume anormal, retornos extremos) — exatamente o perfil pré-EA | SIM (proxies: volume relativo — já têm) |
| Herding Robinhood | Barber-Huang-Odean-Schwarz, JF 2022 (Robintrack, 2018–2020) | Top de compras diárias: **-4,7% de retorno anormal em 20 dias**; episódios de herding mais intensos → perdas maiores. Direção: atenção → pressão de compra → **reversão** | **PARCIAL** — Robintrack acabou em ago/2020; proxies grátis: menções Reddit/WSB, Google Trends |
| Inatenção de sexta-feira | DellaVigna-Pollet, JF 2009 | Anúncios à sexta: reação imediata **-15%**, resposta diferida (drift) **+70%**, volume **-10%** | **SIM** — já têm day-of-week; a implicação direcional é que o vosso feature deve interagir com a magnitude da surpresa |
| Distração (nº de EAs no mesmo dia) | Hirshleifer-Lim-Teoh, JF 2009 | Mais anúncios concorrentes no mesmo dia → reação imediata mais fraca e drift mais forte | **SIM** — contável de calendários de earnings públicos; feature nova barata para o vosso painel |

### 1.5 Textual / NLP / áudio

| Preditor | Paper | Efeito | Ex-ante utilizável? | Grátis? |
|---|---|---|---|---|
| Tom Fin-Neg (Loughran-McDonald) | JF 2011 — **números lidos do paper**: 50.115 10-Ks, 1994–2008 | Retorno mediano da janela [0,+3] do filing: quintil baixo **-0,05%** vs alto **-0,31%** (spread ~**26 pb/4 dias**, monotónico); Fama-MacBeth: coef. -19,54 (t=**-2,64**); tf.idf t=-3,11; R² médio 2,4–2,6% com controlos | O 10-K/10-Q/8-K **anterior** ao EA é ex-ante; o press release do EA não | **SIM** — EDGAR + dicionário L-M público |
| Áudio de calls (afeto vocal) | Mayew-Venkatachalam, JF 2012 | Afeto positivo/negativo dos gestores correlaciona com retornos contemporâneos e earnings futuros inesperados; analistas não incorporam o afeto negativo. Magnitudes: NÃO VERIFICADO | **NÃO** — a call ocorre no/apos o anúncio; só serve para prever drift/trimestre seguinte | PARCIAL (áudio grátis nos sites IR, mas trabalho pesado) |
| Estrutura de press releases | Wu-Akin-**Martineau**-Grégoire-Veneris, arXiv 2509.24254 (2025); 138.000 press releases 2005–2023 | Soft information ≈ tão informativa quanto a surpresa "hard"; **mas os preços refletem totalmente o conteúdo na abertura** | **NÃO** (pós-anúncio); só útil se houvesse leak | SIM (EDGAR) mas inútil ex-ante |
| Guidance bundled | lit. de management guidance (Das et al.; stern) | Em empresas maduras, o guidance de EPS e comentários de buybacks/dividendos **dominam** a reação vs a surpresa realizada; maior proporção de linguagem forward-looking → reação mais forte | Guidance é revelado NO anúncio → NÃO ex-ante; **histórico de guidance** (guider habitual? direção do último guidance?) é ex-ante | PARCIAL (8-Ks EDGAR + NLP) |
| LLMs sobre headlines | Lopez-Lira-Tang (2023, rev. 2025) | GPT-4 pós-cutoff: ~90% de hit portfolio-day na reação inicial **não-transacionável**; prevê o drift subsequente sobretudo em small caps e notícias negativas; **retornos da estratégia caem com a adoção de LLMs** (eficiência) | Drift: sim; reação inicial: não | PARCIAL |
| LLM sobre demonstrações financeiras | Kim-Muhn-Nikolaev (Chicago, 2024) | GPT-4 com chain-of-thought: **60,35%** de acerto na direção dos earnings futuros (analistas ~53% a 1 mês); estratégias com Sharpe e alfas superiores | Prevê **earnings**, não a reação de 1–2 dias; utilizável como input ex-ante | SIM (EDGAR) mas computacionalmente caro |
| Benchmark multimodal | FinCall-Surprise, arXiv 2510.03965 (2025): 2.688 calls 2019–2021, 26 LLMs | Modelos **falham** em aproveitar áudio/slides; accuracies altas são artefacto de class imbalance | — | — |

### 1.6 Os limites (o teto honesto)

| Resultado | Paper | Número |
|---|---|---|
| Decay out-of-sample / pós-publicação | McLean-Pontiff, JF 2016 (97 preditores) | **-26% OOS; -58% pós-publicação** (≈32 pontos atribuíveis a trading informado pela publicação); decay maior nos preditores com maiores retornos in-sample |
| Crise de replicação | Hou-Xue-Zhang, RFS 2020 (452 anomalias) | **65% falham t=1,96** com breakpoints NYSE + value-weighting (96% na categoria trading frictions); **82% falham t=2,78** |
| Decay médio | Chen-Lopez-Lira-Zimmermann (arXiv 2212.10317) | ~**42%** de decay fora de amostra |
| PEAD | Martineau, CFR 2022 | **Zero em large caps desde 2006**; preços refletem a surpresa no dia |
| Eficiência pós-2016 | Christensen-Timmermann-Veliyev, arXiv 2601.08962 (2026) | EAs induzem **saltos** no after-hours; estratégias pós-anúncio consistentes com **preços eficientes após 2016**; co-jumps em não-anunciantes |
| Prémio de anúncio EUA | Heitz-Narayanamoorthy-Zekhnini | Desaparecido pós-2004 (migrou para 8-Ks); vivo fora dos EUA |
| Opções ≈ borrow fees | Muravyev-Pearson-Pollet 2022 | Previsibilidade de spread/skew/O/S cai **~2/3** ajustada aos fees |
| ML sob restrições económicas | Avramov-Cheng-Metzker, MS 2023 | -64% sem microcaps; pior ainda com custos |

---

## 2. O que realmente resta em 2026 — top-5 implementável com dados gratuitos

Ranking por (efeito documentado na janela do EA) × (utilizável ex-ante) × (custo zero de dados), já descontando o que a literatura diz sobre decay:

1. **Bloco de opções live pré-EA** (IV skew + volatility spread + O/S + implied move, do chain do yfinance na véspera). É a única família com evidência direta e quantificada na janela CAR(-1,+1): Johnson-So D1-D10 ≈ -37 pb/3 dias (t≈2,1); skew 10,9%/ano; spread 50 pb/semana; ΔIV call ~1%/mês. **Ressalvas obrigatórias**: ~2/3 é borrow fee (usar short interest FINRA como control), decay pós-publicação, e o yfinance não tem histórico — começar a arquivar chains diariamente já (o backtest só nasce daqui a alguns trimestres) ou aceitar validação apenas prospetiva.
2. **Implied move do straddle como input de magnitude** (não direção): o mercado de opções subestima sistematicamente a incerteza do EA (+3,34% em straddles, Gao-Xing-Zhang). Para o vosso GBM com quantile loss + conformal, o implied move da véspera é provavelmente o melhor regressor de dispersão disponível de graça — e ataca diretamente a largura dos vossos intervalos, onde o valor está, dado que a direção tem teto ~60%.
3. **Atenção retail como sinal de reversão** (Google Trends SVI + volume relativo + proxies Reddit): pico de atenção pré-EA → pressão compradora → pop inicial → reversão (DEG +30 pb/2 semanas revertidos; Barber 2022 -4,7%/20 dias). Implementação: usar atenção elevada pré-EA para **desconfiar** de continuação altista pós-pop, i.e., condicionar o P(up≥5%) em baixa quando a atenção já disparou antes do anúncio.
4. **Revenue SUE de série temporal + interação com SUE de EPS** (EDGAR): incremental ao SUE clássico e ortogonal ao vosso sandbagging de EPS (que já sabem estar priced in); drift mais forte quando ambas as surpresas se alinham. Efeito modesto e sujeito à erosão do PEAD — tratar como feature, não como estratégia.
5. **Features de microestrutura de atenção do calendário** (nº de EAs concorrentes no mesmo dia, sexta-feira, AMC/BMO como interação e não como dummy isolada): DellaVigna-Pollet (-15% reação imediata, +70% drift à sexta) e Hirshleifer-Lim-Teoh (distração por anúncios concorrentes). Custo de implementação quase nulo — é uma contagem sobre o calendário de earnings que já usam — e modula a **magnitude** da reação imediata, útil para os quantis.

Menções honrosas: tom Loughran-McDonald do último filing pré-EA (26 pb/4 dias — pequeno mas grátis); histórico de guidance da empresa (o guidance domina a reação em empresas maduras; o *hábito* de dar guidance é ex-ante).

## 3. O teto documentado — calibrar expectativas

- **R² OOS mensal por ação: 0,26–0,40%** (máx. 0,70% em large caps com NN3). Ao horizonte de 1–2 dias num evento específico, os benchmarks académicos publicados de regressão de CAR de anúncio sobre sinais ex-ante andam em **R² ajustado ~1%** (Johnson-So, com controlos, in-sample).
- **Hit rates direcionais**: o único ~90% publicado (Lopez-Lira) usa a notícia em si — não-transacionável. Acurácia ex-ante documentada em tarefas vizinhas: ~60% na direção de earnings (não do retorno) com GPT-4 vs 53% de analistas. Não encontrei nenhum paper credível com hit rate ex-ante da direção do retorno do anúncio materialmente acima de ~55–60% — **o vosso teto de ~60% na P(up≥5%) calibrada está alinhado com o que a academia consegue** (inferência minha a partir do conjunto; nenhum paper afirma "o máximo é X").
- **O vosso +3,2%/fold não significativo a 2SE é exatamente a ordem de grandeza esperada**: os efeitos por evento documentados são de 25–40 pb (O/S, tom L-M) a low-single-digits (%) por trimestre em famílias inteiras — antes do decay de 26–58% pós-publicação e da mordidela de 2/3 dos borrow fees nos sinais de opções. Com 6.234 eventos, um efeito verdadeiro de 30–50 pb/evento no top-3 é estatisticamente difícil de separar de zero — a literatura prevê precisamente essa frustração.
- Estruturalmente: pós-2016 a reação concentra-se num salto no after-hours (Christensen et al. 2026); a fração previsível ex-ante do movimento de 1–2 dias é pequena, e o que resta concentra-se em small caps ilíquidas com custos que a consomem (Avramov et al.).

## 4. Fontes

- Gu-Kelly-Xiu, RFS 2020: https://academic.oup.com/rfs/article/33/5/2223/5758276 | PDF: https://dachxiu.chicagobooth.edu/download/ML.pdf | SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3159577
- Xing-Zhang-Zhao, JFQA 2010: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1107464 | https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/what-does-the-individual-option-volatility-smirk-tell-us-about-future-equity-returns/ECFD16BA9ACBDC8D577D1BD866FBEA72
- Jin-Livnat-Zhang, JAR 2012: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-679X.2012.00439.x | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1737796
- Johnson-So, JFE 2012: https://www.travislakejohnson.com/pdfs/Johnson%20So%20OS%202012%20(JFE).pdf | https://www.sciencedirect.com/science/article/abs/pii/S0304405X12000797
- Roll-Schwartz-Subrahmanyam O/S: via Johnson-So e https://www.sciencedirect.com/science/article/abs/pii/S0304405X16000167
- An-Ang-Bali-Cakici, JF 2014: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12181 | https://www.nber.org/papers/w19590
- Cremers-Weinbaum, JFQA 2010: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=968237
- Muravyev-Pearson-Pollet 2022: https://fmai.memberclicks.net/assets/docs/Derivatives2022/MuravyevPearsonPollet.pdf
- Gao-Xing-Zhang straddles, JFQA 2018: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2204549
- Jegadeesh-Livnat: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=903767 | https://www.sciencedirect.com/science/article/abs/pii/S0165410106000061
- Frazzini-Lamont: https://www.nber.org/papers/w13090 ; Savor-Wilson, JF 2016: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12361
- Heitz-Narayanamoorthy-Zekhnini: https://www.ssrn.com/abstract=3296537
- Da-Engelberg-Gao, JF 2011: https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2011.01679.x | https://www3.nd.edu/~zda/Google.pdf
- Barber-Huang-Odean-Schwarz, JF 2022: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183
- DellaVigna-Pollet, JF 2009: https://eml.berkeley.edu/~sdellavi/wp/earnfr080204.pdf ; Hirshleifer-Lim-Teoh, JF 2009: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=980958
- Loughran-McDonald, JF 2011: https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2010.01625.x (tabelas lidas do PDF UTS)
- Mayew-Venkatachalam, JF 2012: https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2011.01705.x
- McLean-Pontiff, JF 2016: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365 ; Hou-Xue-Zhang, RFS 2020: https://global-q.org/uploads/1/2/2/6/122679606/houxuezhang2020rfs.pdf
- Martineau, CFR 2022: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607 ; Chen-Lopez-Lira-Zimmermann: https://arxiv.org/pdf/2212.10317
- Avramov-Cheng-Metzker, MS 2023: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3450322
- Lopez-Lira-Tang: https://arxiv.org/abs/2304.07619 ; Kim-Muhn-Nikolaev: https://arxiv.org/abs/2407.17866
- Novidades 2025–2026: press releases https://arxiv.org/abs/2509.24254 ; FinCall-Surprise https://arxiv.org/abs/2510.03965 ; multimodal EA-direction https://arxiv.org/abs/2605.25894 ; warp-speed jumps https://arxiv.org/abs/2601.08962 ; Reviving PEAD c/ ML https://www.sciencedirect.com/science/article/abs/pii/S1544612325020057

**Itens NÃO VERIFICADOS** (não extraí os números primários): magnitudes exatas de Jin-Livnat-Zhang e Mayew-Venkatachalam; ano final da amostra de An-Ang-Bali-Cakici; magnitudes do revenue-SUE de Jegadeesh-Livnat; sobrevivência pós-2015 do ΔIV e do straddle premium. Tudo o resto acima tem fonte direta (3 papers lidos página a página: L-M Tabela II/IV e Figura 1; Johnson-So Tabela 7; GKX Tabelas 1–4 e Figuras 4–5).

---

# SÍNTESE FINAL v9 — cruzamento dos 4 relatórios + decisões

## O benchmark que muda a leitura do sistema
- Medallion: 50,75% de acerto. Venda de prémio: ~58%. Melhor acurácia ex-ante
  académica em tarefas vizinhas: ~60%. **O nosso teto calibrado de ~60% ESTÁ no
  estado da arte** — confirmado independentemente pelos 4 relatórios.
- O nosso +3,2%/fold no TOP-3 é a ordem de grandeza que a literatura documenta
  (efeitos por evento de 25-40bps a low-single-digits por trimestre, antes de
  decay de 26-58% pós-publicação). A não-significância a 2-SE com n=6.234 é a
  frustração que a academia prevê, não um defeito nosso.
- O edge_ratio que já usamos é o sinal de Milian 2023 (t=2,72) — validação externa.

## Tabela mestra dos preditores novos (regra de decisão v9 aplicada)
| Preditor | Efeito documentado | Testável no painel? | DECISÃO |
|---|---|---|---|
| NLP call anterior→surpresa (Koval ACL'23) | 71-77% acc. direcional | Parcial (subsample+prospetivo) | **FASE SEGUINTE** — maior efeito de todos; pipeline de transcripts a construir; entra como contexto até validar |
| Lazy Prices (diffs EDGAR) | 188 bps/mês (JF 2020) | SIM (EDGAR histórico completo) | **FASE SEGUINTE** — testável a 100%; implementação moderada |
| Crowding do calendário + sexta (DellaVigna-Pollet; Hirshleifer) | -15% reação/+70% drift sexta; distração documentada | **SIM, imediato** (datas já no painel) | **IMPLEMENTADO AGORA → tribunal v9** |
| Bloco de opções live: CPIV (Atilgan >1,5%/quintil) + O/S (Johnson-So t=-2,11) | ver relatórios A/C | NÃO (sem histórico grátis de IV) | **CONTEXTO + ARQUIVO DIÁRIO iniciado agora** (o backtest nasce do nosso próprio arquivo) |
| EMI expectations-mgmt (+64-80bps) | Johnson-Kim-So, 320k eventos | Parcial (proxies com look-ahead) | FASE SEGUINTE (com look-ahead declarado) |
| Atenção→reversão (DEG/Barber) | +30bps→reversão; -4,7%/20d | Parcial (rel_volume já é feature) | Já coberto (rel_volume no GBM); Trends/Reddit ficam contexto |
| Revenue SUE | incremental ao SUE | Parcial (EDGAR, esforço) | FASE SEGUINTE |
| Caveat MPP: 2/3 dos sinais de opções = borrow fees | — | — | Short interest FINRA como controlo (roadmap) |

## Mudança de filosofia recomendada pelos 4 relatórios (unânime)
Parar de tentar subir P(acerto) — investir em: (1) opções como PRIOR de magnitude
(implied move → intervalos), (2) breadth (mais eventos, apostas menores),
(3) custos e sizing (Kelly fracionário), (4) interruptor de regime (o prémio de
earnings INVERTEU em Q3-2025/2026 — ORATS).
