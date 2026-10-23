"""
Servico 1 - INGESTAO: recebe documentos, gera embeddings e armazena.

JA PRONTO: indexacao em memoria e a rota de status.
TAREFA 1: persistir o indice em disco para nao perder ao reiniciar.

Rodar: uvicorn servicos.ingestao.app:app --port 8001
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import json

from servicos.comum.embeddings import Vetorizador

app = FastAPI(title="Ingestao - C2.A2")

vetorizador = Vetorizador()
ARQUIVO_INDICE = "indice.json"

def carregar_indice() -> list:
    """Carrega o índice do disco ao iniciar a aplicação."""
    if os.path.exists(ARQUIVO_INDICE):
        with open(ARQUIVO_INDICE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def persistir_indice(dados: list):
    """Salva o índice no disco após cada nova indexação."""
    with open(ARQUIVO_INDICE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

INDICE = carregar_indice()
class Documento(BaseModel):
    texto: str
    origem: str = "desconhecida"


@app.post("/indexar")
def indexar(docs: list[Documento]):
    textos = [d.texto for d in docs]
    vetorizador.ajustar([d["texto"] for d in INDICE] + textos or textos)
    INDICE.clear()
    # reindexa tudo com o vocabulario novo
    for d in docs:
        INDICE.append({"texto": d.texto, "origem": d.origem})
    for item in INDICE:
        item["vetor"] = vetorizador.vetorizar(item["texto"])
    return {"indexados": len(INDICE)}


@app.get("/indice")
def indice():
    """Consumido pelo servico de recuperacao."""
    return {"total": len(INDICE),
            "itens": [{"texto": i["texto"], "origem": i["origem"],
                       "vetor": i["vetor"]} for i in INDICE]}


@app.get("/saude")
def saude():
    return {"status": "ok", "documentos": len(INDICE)}


