"""
Servico 2 - RECUPERACAO: dada uma pergunta, acha os trechos mais relevantes.

TAREFA 2: implementar a busca por similaridade.

Rodar: uvicorn servicos.recuperacao.app:app --port 8002
"""
import os

import requests
from fastapi import FastAPI
from pydantic import BaseModel

from servicos.comum.embeddings import Vetorizador, similaridade

app = FastAPI(title="Recuperacao - C2.A2")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://localhost:8001")


class Consulta(BaseModel):
    pergunta: str
    top_k: int = 3


@app.post("/buscar")
def buscar(consulta: Consulta):
    """Deve devolver os top_k trechos mais parecidos com a pergunta."""
    r = requests.get(f"{URL_INGESTAO}/indice", timeout=10)
    r.raise_for_status()
    itens = r.json()["itens"]
    
    if not itens:
        return {"resultados": []}

    # TAREFA 2: vetorize a pergunta, calcule a similaridade com cada item
    # e devolva os top_k mais parecidos.
    
    # 1. Ajusta o vetorizador com os textos atuais do índice
    vetorizador = Vetorizador()
    vetorizador.ajustar([item["texto"] for item in itens])
    
    # 2. Vetoriza a pergunta feita pelo usuário
    vetor_pergunta = vetorizador.vetorizar(consulta.pergunta)
    
    resultados = []
    # 3. Calcula a similaridade entre a pergunta e cada documento
    for item in itens:
        sim = similaridade(vetor_pergunta, item["vetor"])
        resultados.append({
            "texto": item["texto"],
            "origem": item["origem"],
            "similaridade": sim
        })
        
    # 4. Ordena pela maior similaridade e recorta os top_k
    resultados_ordenados = sorted(resultados, key=lambda x: x["similaridade"], reverse=True)
    
    return {"resultados": resultados_ordenados[:consulta.top_k]}


@app.get("/saude")
def saude():
    return {"status": "ok"}
