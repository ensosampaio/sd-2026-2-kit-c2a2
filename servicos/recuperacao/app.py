"""Servico de recuperacao: consulta a ingestao por REST e calcula similaridade."""
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from servicos.comum.embeddings import Vetorizador, similaridade

app = FastAPI(title="Recuperacao - C2.A2")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://localhost:8001")


class Consulta(BaseModel):
    pergunta: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


@app.post("/buscar")
def buscar(consulta: Consulta):
    """Retorna os documentos mais semelhantes a pergunta recebida."""
    try:
        resposta = requests.get(f"{URL_INGESTAO}/indice", timeout=10)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Servico de ingestao indisponivel: {erro}",
        ) from erro

    itens = resposta.json().get("itens", [])
    if not itens:
        return {"resultados": []}

    textos = [item["texto"] for item in itens]
    vetorizador = Vetorizador()
    vetorizador.ajustar(textos)
    vetor_pergunta = vetorizador.vetorizar(consulta.pergunta)

    resultados = []
    for item in itens:
        vetor_documento = vetorizador.vetorizar(item["texto"])
        resultados.append({
            "texto": item["texto"],
            "origem": item.get("origem", "desconhecida"),
            "similaridade": similaridade(vetor_pergunta, vetor_documento),
        })

    resultados.sort(key=lambda item: item["similaridade"], reverse=True)
    return {"resultados": resultados[:consulta.top_k]}


@app.get("/saude")
def saude():
    return {"status": "ok"}