"""Worker consumidor da fila Redis de ingestao.

Execute com: python -m servicos.ingestao.worker
"""
import json
import os
import time
from pathlib import Path

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FILA_PENDENTES = os.getenv("FILA_INGESTAO", "rag:ingestao:pendentes")
FILA_PROCESSANDO = os.getenv("FILA_INGESTAO_PROCESSANDO", "rag:ingestao:processando")
ARQUIVO_INDICE = Path(
    os.getenv("ARQUIVO_INDICE", str(Path(__file__).with_name("indice.json")))
)

cliente_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def carregar_indice() -> list:
    if not ARQUIVO_INDICE.exists():
        return []
    with ARQUIVO_INDICE.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if not isinstance(dados, list):
        raise ValueError("O indice precisa conter uma lista de documentos.")
    return dados


def salvar_indice(dados: list) -> None:
    ARQUIVO_INDICE.parent.mkdir(parents=True, exist_ok=True)
    arquivo_temporario = ARQUIVO_INDICE.with_suffix(".tmp")
    with arquivo_temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    arquivo_temporario.replace(ARQUIVO_INDICE)


def processar(payload: str) -> None:
    novos_documentos = json.loads(payload)
    if not isinstance(novos_documentos, list):
        raise ValueError("Mensagem da fila precisa ser uma lista de documentos.")

    indice = carregar_indice()
    for documento in novos_documentos:
        texto = str(documento.get("texto", "")).strip()
        if not texto:
            continue
        indice.append({
            "texto": texto,
            "origem": documento.get("origem", "desconhecida"),
        })
    salvar_indice(indice)
    print(f"Mensagem processada: {len(novos_documentos)} documento(s). Total: {len(indice)}")


def main() -> None:
    print(f"Worker iniciado. Aguardando mensagens em '{FILA_PENDENTES}'...")
    while True:
        mensagem = cliente_redis.brpoplpush(
            FILA_PENDENTES, FILA_PROCESSANDO, timeout=5
        )
        if mensagem is None:
            continue
        try:
            processar(mensagem)
        except Exception as erro:
            print(
                f"Erro ao processar mensagem; ela ficou na fila "
                f"de processamento: {erro}"
            )
            time.sleep(2)
            continue
        cliente_redis.lrem(FILA_PROCESSANDO, 1, mensagem)


if __name__ == "__main__":
    main()