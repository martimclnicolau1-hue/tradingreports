#!/bin/bash
# v14: entrypoint único do runner cloud (routine 17:03 Europa/Lisboa, seg-sex).
# Contrato: executa as etapas por ordem, com 1 retry nas críticas; deadline
# duro 19:50 Lisboa — se não há escolhido pronto, aborta e envia alerta de
# FALHA pelo mesmo webhook. No fim, committa o estado acumulado.
set -uo pipefail
cd "$(dirname "$0")"
export TZ=Europe/Lisbon
export EVENTCAL_ROLLING=1 EVENTCAL_TODAY=1
PY="${PY:-python3}"
FASE="${1:-tudo}"   # v15.2: "preparar" (até ao escolhido) | "enviar" (envio+estado) | "tudo"

fail() {
  echo "FALHA: $1"
  $PY -m src.send_webhook --failure "$1" || true
  exit 1
}
deadline() {
  [ "${DRYRUN:-0}" = "1" ] && return 0   # teste fora de horas não aborta
  if [ "$(date +%H%M)" -ge 1950 ]; then fail "deadline 19:50 excedido ($1)"; fi
}
retry() { "$@" || { echo "retry: $*"; sleep 30; "$@"; }; }

# 0) despensa: se o clone vem vazio, desempacota o estado
$PY -m src.state_bundle --unpack || true

# 1) pipeline principal (críticos com retry; contexto degrada sem abortar)
retry $PY run.py                                || fail "run.py"
deadline "pós-universo"
retry $PY -m src.rescore_v3                     || fail "rescore_v3"
$PY -m src.options_clean                        || echo "[degradado] options_clean"
$PY -m src.enrich_social                        || echo "[degradado] social"
retry $PY -m src.ev_engine --skip-validation    || fail "ev_engine"
retry $PY -m src.gbm_engine --score             || fail "gbm_engine"
$PY -m src.hype_calc                            || echo "[degradado] hype"
$PY -m src.chain_archive                        || echo "[degradado] chains"
$PY -m src.emi                                  || echo "[degradado] emi"
$PY -m src.finra_short                          || echo "[degradado] finra_short"
$PY -m src.finra_si                             || echo "[degradado] finra_si"
deadline "pós-scoring"

# 2) produtos
$PY -m src.daily_brief                          || fail "daily_brief"
$PY -m src.escolhido                            || fail "escolhido"
deadline "pré-envio"

if [ "$FASE" = "preparar" ]; then
  echo "FASE PREPARAR OK $(date '+%H:%M') — escolhido pronto; segue a pesquisa do agente e depois: bash run_pipeline.sh enviar"
  exit 0
fi

# 3) envio (a secção de pesquisa já foi inserida pelo agente entre as fases)
$PY -m src.send_webhook                         || fail "envio webhook"

# 4) pós-envio (não atrasa o email)
$PY -m studies.rnp_test                         || true
$PY -m src.snapshot_estimates                   || true
$PY -m src.monitor                              || true

# 5) estado → repo (cada corrida arranca de clone fresco)
$PY -m src.state_bundle --pack                  || true
gzip -kf output/factor_panel.csv 2>/dev/null    || true
git add -A data/chains data/estimates data/picks_log.csv data/state.tar.gz output/factor_panel.csv.gz 2>/dev/null
git -c user.name="routine" -c user.email="routine@cloud" commit -m "estado $(date +%F)" 2>/dev/null \
  && git push || echo "[aviso] push do estado falhou (não fatal)"

echo "PIPELINE OK $(date '+%F %H:%M %Z')"
