# Auditoria das fontes de dados — estatuto point-in-time (deliverable 2)
*2026-08-06. Regra 2 do spec: fonte crítica não-PIT ⇒ parar e reportar.
As duas falhas críticas encontradas têm plano de correção (v15 P2-P3)
ou confinamento declarado.*

| Fonte | Uso | Veredicto PIT | Ação |
|---|---|---|---|
| EDGAR form.idx + submissions (8-K 2.02) | universo canónico do backtest | **PIT CONFIRMADO** — filings imutáveis com acceptanceDateTime; inclui mortas | Torna-se o universo (v15 P2) |
| Nasdaq calendar | universo live do dia | Sem histórico (live-only) | Mantém-se só no live |
| yfinance earnings dates | datas de eventos históricos | Datas: sólidas | Cruzadas com EDGAR no v15 |
| yfinance consenso/surpresas históricas | features de surpresa | **SUSPEITA DE REVISÃO — vintage única** não reconstruível às 17:03 de D | CONFINADO: features usam só factos de trimestres FECHADOS; consenso corrente nunca é feature (declarado em criterios) |
| yfinance preços (auto-adjust) | features de preço + y | Rácios close-to-close PIT-seguros; **SURVIVORSHIP** (mortas ausentes) | Corrigido no v15 P3 (Stooq/AV para mortas) |
| FINRA short diário | short_ratio_z5/z20 | **PIT CONFIRMADO** (ficheiros datados T+0, keyed antes do evento) | — |
| FINRA SI bi-mensal | contexto | PIT-ável por data de publicação (+8 dias úteis) | Contexto; uso histórico exige key na publicação |
| yfinance info (mcap, fundamentais) | flags forenses, EMI v1, prosa | **SNAPSHOT SEM DATA = look-ahead histórico** | CONFINADO ao live; fora do backtest (decisão do utilizador) |
| Snapshots próprios (consenso diário, chains) | painel PIT futuro | PIT confirmado, nascidos 2026-08-05/06 | Inúteis para o backtest 7 anos; críticos para 2027 |
| Stooq bulk / Alpha Vantage | preços de mortas (v15) | PIT-seguro para closes; ajustes a validar contra 2ª fonte | Matching ≥85%/ano ou PARAR (correção 3) |

## Vereditos de paragem (regra 2) e a sua resolução
1. **Survivorship dos preços** → RESOLVE-SE no v15 P2-P3 (universo EDGAR
   + preços de mortas enquanto vivas; y é fecho-a-fecho, o delisting
   return não é necessário — correção do utilizador).
2. **Consenso histórico não-PIT** → NÃO RESOLÚVEL grátis para trás;
   CONFINADO por desenho (só factos fechados como features) e declarado
   em criterios_sucesso.md. O painel PIT próprio resolve-o para a frente.
