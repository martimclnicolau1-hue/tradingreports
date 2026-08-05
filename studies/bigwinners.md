# Estudo big-winners v10 — eventos com y ≥ +20% no dia do report

*Gerado 2026-08-05 por studies/bigwinners.py; índice e limiares pré-registados na metodologia v10 §10 ANTES de correr. y = reação close→close (AMC: D→D+1; BMO: D−1→D), fórmula única de reactions.py.*

## 1. QA do painel
- Painel completo: **25875** eventos, 1026 tickers, 2017-10-23 → 2026-08-05.
- Janela primária do estudo (≥2019-08-01, 7 anos): **22086** eventos, 1022 tickers.
- NaN por feature (janela do estudo): prior_avg_move 0.0%; dist_52w_high 0.0%; rsi14 0.0%; mom60 0.0%; rel_volume 0.0%; sandbag 0.0%; prior_up_big_rate 0.0%; vix 0.0%; n_events_same_day 0.0%; log_close 0.0%; log_dollar_vol 0.0%.
- **VIÉS DE SOBREVIVÊNCIA DECLARADO**: o painel nasce do universo de HOJE — deslistados/adquiridos 2019-2025 estão ausentes. Todas as taxas abaixo são CONDICIONAIS a "sobreviveu até 2026". Blow-ups que saíram de bolsa não contam para a cauda negativa — ela está SUBESTIMADA.

## 2. Taxas-base
- Janela do estudo: **P(y≥+20%) = 3.22%** (712 eventos) | **P(y≤−20%) = 2.35%** (520) | média y = +0.43%.

### Por ano
| year | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| 2019 | 1029 | 1.8 | 2.2 | 0.2 |
| 2020 | 2471 | 2.6 | 1.0 | 0.8 |
| 2021 | 2677 | 1.0 | 1.1 | 0.1 |
| 2022 | 3059 | 2.3 | 2.8 | 0.2 |
| 2023 | 3445 | 3.5 | 1.9 | 0.8 |
| 2024 | 3587 | 4.3 | 2.8 | 0.6 |
| 2025 | 3775 | 4.4 | 3.1 | 0.3 |
| 2026 | 2043 | 4.6 | 3.5 | 0.2 |

### Por regime VIX (bins fixos pré-registados)
| regime | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| VIX<15 | 3207 | 3.6 | 2.4 | 0.5 |
| VIX 15-25 | 15041 | 3.4 | 2.4 | 0.5 |
| VIX>25 | 3838 | 2.4 | 2.3 | 0.1 |

## 3. Perfis por quartil — P(≥+20%) SEMPRE ao lado de P(≤−20%)
*As colunas p_up20/p_dn20/media_y estão em %. A pergunta honesta não é só "onde vivem os moonshots" mas "o que mais vive lá".*

### prior_avg_move
| prior_avg_move | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 0.3 | 0.3 | 0.1 |
| Q2 | 5521 | 1.3 | 0.9 | 0.2 |
| Q3 | 5521 | 3.0 | 2.4 | 0.3 |
| Q4 (alto) | 5522 | 8.3 | 5.8 | 1.1 |

### dist_52w_high
| dist_52w_high | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5521 | 5.1 | 4.5 | 0.5 |
| Q2 | 5521 | 3.1 | 2.2 | 0.5 |
| Q3 | 5520 | 2.6 | 1.5 | 0.4 |
| Q4 (alto) | 5521 | 2.1 | 1.2 | 0.4 |

### rsi14
| rsi14 | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 3.2 | 3.0 | 0.2 |
| Q2 | 5521 | 3.3 | 2.5 | 0.6 |
| Q3 | 5521 | 3.4 | 2.1 | 0.5 |
| Q4 (alto) | 5522 | 3.1 | 1.8 | 0.4 |

### mom60
| mom60 | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 3.7 | 3.3 | 0.6 |
| Q2 | 5521 | 2.4 | 1.9 | 0.3 |
| Q3 | 5521 | 2.4 | 1.6 | 0.4 |
| Q4 (alto) | 5522 | 4.4 | 2.6 | 0.4 |

### rel_volume
| rel_volume | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 2.9 | 1.6 | 0.6 |
| Q2 | 5521 | 2.9 | 2.0 | 0.4 |
| Q3 | 5521 | 2.9 | 2.5 | 0.4 |
| Q4 (alto) | 5522 | 4.1 | 3.4 | 0.3 |

### sandbag
| sandbag | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5520 | 4.0 | 2.4 | 0.7 |
| Q2 | 5520 | 1.8 | 1.5 | 0.2 |
| Q3 | 5520 | 2.9 | 2.3 | 0.3 |
| Q4 (alto) | 5520 | 4.2 | 3.2 | 0.5 |

### vix
| vix | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5545 | 3.4 | 2.5 | 0.5 |
| Q2 | 5606 | 3.3 | 2.4 | 0.3 |
| Q3 | 5436 | 3.1 | 2.3 | 0.4 |
| Q4 (alto) | 5499 | 3.1 | 2.2 | 0.5 |

### n_events_same_day
| n_events_same_day | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5597 | 3.6 | 2.3 | 0.4 |
| Q2 | 5619 | 2.8 | 2.2 | 0.2 |
| Q3 | 5400 | 3.0 | 2.5 | 0.2 |
| Q4 (alto) | 5470 | 3.4 | 2.5 | 0.9 |

### log_close
| log_close | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 5.3 | 2.7 | 1.1 |
| Q2 | 5523 | 3.5 | 2.8 | 0.2 |
| Q3 | 5519 | 2.2 | 2.1 | 0.4 |
| Q4 (alto) | 5522 | 1.9 | 1.9 | 0.0 |

### log_dollar_vol
| log_dollar_vol | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5522 | 3.6 | 2.1 | 0.7 |
| Q2 | 5521 | 3.5 | 2.4 | 0.6 |
| Q3 | 5521 | 2.7 | 2.3 | 0.1 |
| Q4 (alto) | 5522 | 3.0 | 2.6 | 0.2 |

### log_mcap (CONTEXTO APENAS — look-ahead declarado: mcap de hoje em eventos históricos)
| log_mcap | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| Q1 (baixo) | 5263 | 4.2 | 3.6 | -0.0 |
| Q2 | 5232 | 3.6 | 2.9 | 0.4 |
| Q3 | 5262 | 2.7 | 1.6 | 0.5 |
| Q4 (alto) | 5226 | 1.7 | 0.9 | 0.8 |

### Timing e dia da semana
| AMC=1 | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| 0.0 | 9063.0 | 2.5 | 1.9 | 0.4 |
| 1.0 | 13023.0 | 3.7 | 2.7 | 0.5 |
| dow (0=2ª) | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| 0.0 | 2462.0 | 3.9 | 3.0 | 0.4 |
| 1.0 | 3954.0 | 3.4 | 2.7 | 0.1 |
| 2.0 | 6455.0 | 3.0 | 2.1 | 0.5 |
| 3.0 | 8018.0 | 3.3 | 2.3 | 0.6 |
| 4.0 | 1134.0 | 2.1 | 1.5 | 0.2 |
| 5.0 | 6.0 | 0.0 | 0.0 | 1.6 |
| 6.0 | 57.0 | 0.0 | 0.0 | 0.1 |

## 4. Interação log_close × prior_avg_move (única interação pré-registada)

P(y≥+20%) em %:
| q_vol | preço Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| vol Q1 | 0.7 | 0.1 | 0.1 | 0.3 |
| Q2 | 2.5 | 1.5 | 0.8 | 0.7 |
| Q3 | 4.3 | 3.3 | 2.5 | 1.9 |
| Q4 | 11.5 | 8.3 | 5.5 | 6.5 |

n por célula:
| q_vol | preço Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| vol Q1 | 1238 | 1386 | 1368 | 1530 |
| Q2 | 1221 | 1162 | 1445 | 1693 |
| Q3 | 1364 | 1422 | 1384 | 1351 |
| Q4 | 1699 | 1553 | 1322 | 948 |

P(y≤−20%) em % (a mesma célula, o outro lado da moeda):
| q_vol | preço Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| vol Q1 | 0.2 | 0.6 | 0.2 | 0.1 |
| Q2 | 1.5 | 0.9 | 0.6 | 0.9 |
| Q3 | 2.6 | 2.5 | 2.3 | 2.1 |
| Q4 | 5.5 | 6.3 | 5.4 | 5.9 |

## 5. Repeat offenders — os moonshots repetem-se?
- P(y≥+20% | ≥1 big-up nos 8 eventos prévios) = **9.11%** (n=3096)
- P(y≥+20% | 0 big-ups nos 8 prévios) = **2.19%** (n=17968)
- ...e a cauda negativa nas mesmas condições: 6.40% vs 1.63%.
- Concentração: 373 tickers geram 712 moonshots; o top-10% dos tickers gera 25% deles.
- Top-20 por contagem: CVNA (8), ARLO (7), PLTR (6), VISN (6), GRPN (6), APP (6), BW (6), TDUP (5), MDB (5), OUST (5), CELH (5), OMER (5), TPC (5), CPS (5), SNAP (5), GCT (5), WLDN (5), APEI (5), NUTX (4), SYM (4).

## 6. Mecanismo (SÓ conhecido APÓS o print — não negociável ex-ante)
| surpresa EPS | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| miss (≤0) | 7223 | 1.8 | 3.8 | -2.4 |
| beat 0-5% | 2623 | 1.0 | 1.4 | -0.7 |
| beat 5-15% | 3802 | 2.3 | 1.6 | 0.9 |
| beat >15% | 8132 | 5.7 | 1.8 | 3.1 |
- Dos 708 moonshots com surpresa conhecida: 82% tiveram beat; 66% tiveram beat >15%.

## 7. Perfil-lotaria pré-declarado (quartil topo de prior_avg_move ∧ metade inferior de log_close)
- Perfil: n=3252 (15% dos eventos). **P(≥+20%) = 9.99%** vs resto 2.05%.
- **P(≤−20%) = 5.90%** vs resto 1.74% — rácio up:down no perfil = **1.69**.
- Média y no perfil: +1.54% | mediana +0.34% (a média pode viver das caudas; a mediana conta a história do evento típico).

### EV bruto por ano de "comprar todos os eventos do perfil" (SEM custos/slippage — declarado)
| year | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| 2019 | 110 | 8.2 | 4.5 | 0.7 |
| 2020 | 314 | 8.0 | 2.5 | 1.8 |
| 2021 | 208 | 3.8 | 2.9 | 0.7 |
| 2022 | 405 | 6.4 | 8.1 | 0.3 |
| 2023 | 600 | 11.2 | 4.0 | 2.9 |
| 2024 | 619 | 12.8 | 8.4 | 1.2 |
| 2025 | 649 | 12.0 | 6.0 | 2.3 |
| 2026 | 347 | 9.5 | 7.2 | 0.3 |

## 8. Setor (info de hoje — look-ahead residual declarado; setor é quase-estático)
| sector | n | p_up20 | p_dn20 | media_y |
|---|---|---|---|---|
| ? | 1175 | 6.4 | 4.2 | 0.7 |
| Technology | 3405 | 4.9 | 3.5 | 0.8 |
| Communication Services | 1364 | 4.3 | 3.5 | 0.3 |
| Industrials | 2472 | 4.3 | 2.3 | 1.0 |
| Consumer Cyclical | 2017 | 3.8 | 3.0 | 0.4 |
| Healthcare | 4576 | 3.1 | 2.7 | 0.2 |
| Consumer Defensive | 827 | 3.0 | 2.4 | 1.2 |
| Financial Services | 1852 | 1.6 | 0.9 | 0.3 |
| Utilities | 765 | 1.0 | 0.8 | 0.0 |
| Basic Materials | 1219 | 0.8 | 0.8 | -0.3 |
| Energy | 1446 | 0.6 | 0.6 | 0.1 |
| Real Estate | 968 | 0.3 | 0.0 | 0.3 |

---
*Este estudo é descritivo. A passagem a features/modelo faz-se exclusivamente via tribunal v10 (gates pré-registados na metodologia). Perfis com P(≥+20%) alta têm SEMPRE P(≤−20%) alta ao lado — volatilidade não é direção. Nada aqui é recomendação.*