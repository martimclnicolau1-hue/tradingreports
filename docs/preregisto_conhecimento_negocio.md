# Pré-registo — módulo "conhecimento holístico do negócio" (proposta do utilizador, 2026-08-06)

*Escrito ANTES de qualquer teste, por decisão do utilizador na conversa de
2026-08-06 ("experimenta e vê se passa nos testes, mas só depois de o que
está a acontecer acabar"). Este documento fixa a intenção e o desenho do
teste para impedir ajustes pós-resultados (lei 1 da casa). NÃO altera nada
na validação v15 em curso, cujos critérios estão congelados (commit 4ee6478).*

## A hipótese (do utilizador)
O sistema deve "conhecer mesmo o negócio" de cada Escolhido — o que vende,
a quem, contra quem, com que vantagem, e o que este trimestre tem de
específico — e esse conhecimento holístico melhora a decisão face ao motor
puramente quantitativo (FEATS_V14: expectativas/posicionamento/preço).

## Aviso honesto pré-registado
Na janela de ~24h do evento, a literatura aponta para expectativas e
posicionamento como dominantes; a hipótese do utilizador é contrária ou
complementar a isto. É exatamente por isso que se testa — o veredicto é
dos dados, não da estética da ideia.

## Desenho do teste (modo sombra; nada manda no pick)
1. **Quando começa**: só depois de a validação v15 (P2-P7) estar fechada
   e reportada. Nenhuma mudança antes disso.
2. **O que o agente produz por dia** (na fase de pesquisa da routine, para
   o candidato nº 1 e para o nº 2 do ranking):
   - dossiê curto do negócio (o que vende, clientes, concorrência, moat,
     o que ver no print desta noite);
   - **nota de convicção 0-10** ("com o que sei do negócio, este setup do
     motor faz sentido?") + direção (concorda / discorda / neutro).
3. **Registo**: colunas novas no ledger (`data/picks_log.csv`):
   `agente_convicao`, `agente_direcao`, mais o dossiê arquivado em
   `output/dossiers/`. A escolha continua 100% pela regra v13.2/v14.
4. **Julgamento** (após ≥20 eventos com sombra preenchida):
   - dias em que agente e motor discordaram: quem acertou mais (y realizado)?
   - a convicção estratifica os retornos? (média líquida por tercil de nota)
   - critério de adoção: melhoria líquida com IC que exclua zero, no
     espírito dos gates do tribunal; senão, o módulo fica como prosa do
     email (valor jornalístico, não decisório).
5. **Proibições**: a nota do agente nunca vê o y realizado antes de ser
   escrita (é dada até às 19:50 do próprio dia); os critérios deste
   pré-registo não se afinam depois de começar o registo — mudá-los
   exige novo pré-registo datado e recomeço da contagem.

## Relação com o roadmap existente
Complementa (não substitui) a Fase C: EX-99.1/sandbag 2 regimes, Form 4,
Lazy Prices, NLP das calls — esses são conhecimento do negócio tornado
mensurável; este módulo testa a versão qualitativa via agente.
