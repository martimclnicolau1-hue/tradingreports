# -*- coding: utf-8 -*-
"""v14: envio do Escolhido por webhook Make (runner cloud, sem MCP).

MAKE_WEBHOOK_URL vem do ambiente cloud (nunca do repo). Payload JSON:
{"to", "subject", "body"} — o cenário Make encaminha para o Gmail
existente. --failure envia alerta de falha em vez do brief.

Uso: python3 -m src.send_webhook [--failure "motivo"]
"""
import json
import os
import sys
import urllib.request
from datetime import date

DESTINATARIOS = ["luis@nikufra.ai", "matosrmf@gmail.com"]
DEST_FALHA = ["luis@nikufra.ai"]


def _post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    url = os.environ.get("MAKE_WEBHOOK_URL")
    if not url:
        print("[ERRO] MAKE_WEBHOOK_URL não definido no ambiente — sem envio. "
              "Configura o secret no cloud environment (nunca no repo).")
        sys.exit(3)
    hoje = date.today().isoformat()
    dry = os.environ.get("DRYRUN") == "1"
    if dry:
        global DESTINATARIOS
        DESTINATARIOS = DEST_FALHA  # dry-run: só o dono recebe
    if "--failure" in sys.argv:
        motivo = sys.argv[sys.argv.index("--failure") + 1] if len(sys.argv) > 2 else "desconhecido"
        for to in DEST_FALHA:
            _post(url, {"to": to, "subject": "FALHA no pipeline — sem brief hoje",
                        "body": f"<p>O pipeline abortou: <b>{motivo}</b> "
                                f"({hoje}). Sem Escolhido hoje; ver logs da routine.</p>"})
        print("alerta de FALHA enviado")
        return
    path = f"output/escolhido_{hoje}.html"
    if not os.path.exists(path):
        print(f"[ERRO] {path} não existe")
        sys.exit(2)
    body = open(path).read()
    # ticker no subject (1ª linha do md)
    tk = "—"
    primeira = ""  # v15.2c: sem o .md, "primeira" ficava por definir (NameError)
    md = f"output/escolhido_{hoje}.md"
    if os.path.exists(md):
        primeira = open(md).readline()
        if "—" in primeira:
            tk = primeira.split("—")[1].strip().split(" ")[0]
    sem_trade = "Sem escolhido" in primeira
    subject = ("NÃO HÁ TRADE HOJE — dia sem candidato elegível" if sem_trade
               else f"O Escolhido de hoje — {tk} (prazo 21:00)")
    for to in DESTINATARIOS:
        st = _post(url, {"to": to, "subject": subject, "body": body})
        print(f"enviado a {to}: HTTP {st}")


if __name__ == "__main__":
    main()
