"""
Servico 3 - GERACAO: monta o prompt com o contexto e chama o LLM.

A chamada ao LLM (dependencia externa lenta e instavel) e protegida por:
  - TEMPO-LIMITE: cada tentativa usa LLM_TIMEOUT segundos (ver comum/llm.py);
  - RETENTATIVA: ate LLM_TENTATIVAS tentativas, com backoff exponencial;
  - CIRCUIT BREAKER: apos varias falhas seguidas o circuito abre e as
    chamadas sao recusadas na hora, sem sobrecarregar o LLM.

Se o LLM nao responder, o servico degrada com elegancia: devolve 503 com
uma mensagem clara e os trechos recuperados, em vez de quebrar.

Rodar: uvicorn servicos.geracao.app:app --port 8003
"""
import logging
import os
import time

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from servicos.comum.circuit_breaker import CircuitBreaker, CircuitoAberto
from servicos.comum.llm import gerar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("geracao")

app = FastAPI(title="Geracao - C2.A2")

URL_RECUPERACAO = os.getenv("URL_RECUPERACAO", "http://localhost:8002")
TIMEOUT_RECUPERACAO = float(os.getenv("TIMEOUT_RECUPERACAO", "10"))
LLM_TENTATIVAS = int(os.getenv("LLM_TENTATIVAS", "3"))
LLM_BACKOFF_SEGUNDOS = float(os.getenv("LLM_BACKOFF_SEGUNDOS", "0.5"))
CB_LIMITE_FALHAS = int(os.getenv("CB_LIMITE_FALHAS", "5"))
CB_ESPERA_SEGUNDOS = float(os.getenv("CB_ESPERA_SEGUNDOS", "20"))

disjuntor = CircuitBreaker(limite_falhas=CB_LIMITE_FALHAS,
                           espera_segundos=CB_ESPERA_SEGUNDOS)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


def gerar_protegido(pergunta: str, contexto: list) -> str:
    """Chama o LLM com retentativa; cada tentativa passa pelo disjuntor.

    CircuitoAberto NAO e retentado: se o circuito abriu, insistir so
    atrasaria a resposta. Qualquer outra excecao esgota as tentativas e
    e relancada para o endpoint tratar.
    """
    ultimo_erro = None
    for tentativa in range(1, LLM_TENTATIVAS + 1):
        try:
            return disjuntor.chamar(gerar, pergunta, contexto)
        except CircuitoAberto:
            raise
        except Exception as erro:  # noqa: BLE001
            ultimo_erro = erro
            log.warning("LLM falhou (tentativa %d/%d, circuito=%s): %s",
                        tentativa, LLM_TENTATIVAS, disjuntor.estado, erro)
            if tentativa < LLM_TENTATIVAS:
                time.sleep(LLM_BACKOFF_SEGUNDOS * (2 ** (tentativa - 1)))
    raise ultimo_erro


@app.post("/perguntar")
def perguntar(p: Pergunta):
    inicio = time.time()

    try:
        r = requests.post(f"{URL_RECUPERACAO}/buscar",
                          json={"pergunta": p.pergunta, "top_k": p.top_k},
                          timeout=TIMEOUT_RECUPERACAO)
        r.raise_for_status()
        resultados = r.json()["resultados"]
    except (requests.RequestException, KeyError, ValueError) as erro:
        log.error("recuperacao indisponivel: %s", erro)
        return JSONResponse(
            status_code=503,
            content={"detail": f"Servico de recuperacao indisponivel: {erro}"},
        )

    if not resultados:
        return JSONResponse(
            status_code=404,
            content={"detail": "Nenhum documento indexado para embasar a resposta."},
        )

    contexto = [t["texto"] for t in resultados]
    fontes = [{"origem": t.get("origem", "desconhecida"),
               "similaridade": round(t.get("similaridade", 0.0), 4)}
              for t in resultados]

    try:
        resposta = gerar_protegido(p.pergunta, contexto)
    except CircuitoAberto:
        log.error("circuito aberto: chamada ao LLM recusada")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "LLM temporariamente indisponivel (circuit breaker aberto). "
                          "Tente novamente em instantes.",
                "disjuntor": disjuntor.estado,
                "contexto": contexto,
                "fontes": fontes,
            },
        )
    except Exception as erro:  # noqa: BLE001
        log.error("LLM falhou apos %d tentativas: %s", LLM_TENTATIVAS, erro)
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"LLM falhou apos {LLM_TENTATIVAS} tentativas: {erro}",
                "disjuntor": disjuntor.estado,
                "contexto": contexto,
                "fontes": fontes,
            },
        )

    log.info("pergunta respondida em %.0fms (%d trechos, circuito=%s)",
             (time.time() - inicio) * 1000, len(contexto), disjuntor.estado)
    return {"pergunta": p.pergunta, "resposta": resposta,
            "contexto": contexto, "fontes": fontes}


@app.get("/saude")
def saude():
    return {"status": "ok", "disjuntor": disjuntor.estado}
