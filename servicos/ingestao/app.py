"""API de ingestao: publica documentos na fila Redis para processamento assincrono."""
import json
import os
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Ingestao - C2.A2")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FILA_INGESTAO = os.getenv("FILA_INGESTAO", "rag:ingestao:pendentes")
ARQUIVO_INDICE = Path(
    os.getenv("ARQUIVO_INDICE", str(Path(__file__).with_name("indice.json")))
)

cliente_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class Documento(BaseModel):
    texto: str = Field(min_length=1)
    origem: str = "desconhecida"


def carregar_indice() -> list:
    """Le os documentos persistidos; vetores sao calculados na recuperacao."""
    if not ARQUIVO_INDICE.exists():
        return []
    try:
        with ARQUIVO_INDICE.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, list):
            raise ValueError("O indice precisa conter uma lista de documentos.")
        return dados
    except (json.JSONDecodeError, ValueError) as erro:
        raise HTTPException(status_code=500, detail=f"Indice invalido: {erro}") from erro


@app.post("/indexar", status_code=202)
def indexar(docs: list[Documento]):
    """Publica documentos na fila; o worker fara a persistencia em segundo plano."""
    if not docs:
        raise HTTPException(status_code=400, detail="Envie pelo menos um documento.")

    payload = [documento.model_dump() for documento in docs]
    try:
        cliente_redis.rpush(FILA_INGESTAO, json.dumps(payload, ensure_ascii=False))
    except redis.RedisError as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Nao foi possivel publicar na fila Redis: {erro}",
        ) from erro

    return {
        "status": "enfileirado",
        "documentos_enfileirados": len(payload),
        "fila": FILA_INGESTAO,
        "mensagem": "O worker processara os documentos de forma assincrona.",
    }


@app.get("/indice")
def indice():
    """Endpoint REST consumido pelo servico de recuperacao."""
    itens = carregar_indice()
    return {"total": len(itens), "itens": itens}


@app.get("/saude")
def saude():
    try:
        cliente_redis.ping()
        redis_status = "ok"
    except redis.RedisError:
        redis_status = "indisponivel"
    return {
        "status": "ok" if redis_status == "ok" else "degradado",
        "redis": redis_status,
        "documentos": len(carregar_indice()),
    }