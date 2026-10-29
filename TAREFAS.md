# TAREFAS - Trabalho C2.A2 (RAG Distribuido)

## Nucleo obrigatorio

- [x] **1. Persistencia dos documentos** - `servicos/ingestao/worker.py` grava o indice em JSON.
- [x] **2. Busca por similaridade** - `servicos/recuperacao/app.py` calcula TF-IDF e similaridade do cosseno.
- [x] **3. Circuit breaker no LLM** - `servicos/geracao/app.py` envolve `gerar(...)` com `disjuntor.chamar(...)`, com timeout, retentativa (backoff) e 503 quando o circuito esta aberto.
- [x] **4. Mensageria com Redis** - `POST /indexar` publica uma mensagem; `servicos/ingestao/worker.py` consome a fila e persiste os documentos.
- [x] **5. Fluxo completo validado** - testado ponta a ponta (indexar -> fila -> worker -> recuperar -> gerar), incluindo falhas do LLM e servico fora do ar.
- [x] **6. README final com diagrama e execucao do zero** - diagrama Mermaid, tabela dos servicos, resiliencia e passo a passo (Docker e local).

## Pendentes para fechar a entrega (o README ja descreve o resultado final)

- [ ] **7. Containerizacao (Arthur)** - criar `Dockerfile`, `.dockerignore` e completar o `docker-compose.yml` com os servicos `ingestao` (8001), `worker`, `recuperacao` (8002) e `geracao` (8003), alem do `redis` que ja existe. Ingestao e worker compartilham um volume com `ARQUIVO_INDICE=/dados/indice.json`; os servicos se enxergam por nome (`URL_INGESTAO=http://ingestao:8001`, `URL_RECUPERACAO=http://recuperacao:8002`, `REDIS_URL=redis://redis:6379/0`) e o `uvicorn` sobe com `--host 0.0.0.0`. Validar com `docker compose up --build -d`.
- [ ] **8. Scripts de demonstracao (Lucas)** - criar `scripts/indexar_documentos.py` (le `documentos/*.txt`, envia para `POST /indexar` com `origem` = nome do arquivo e espera o worker processar consultando `GET /indice`) e `scripts/perguntar.py` (faz `POST /perguntar` com a pergunta passada na linha de comando e imprime o status HTTP e o JSON).

## Extensoes opcionais

- [x] Citar quais documentos embasaram as respostas finais (campo `fontes`).
- [ ] Avaliacao automatica simples da qualidade da resposta.
- [ ] Trocar TF-IDF por embeddings de verdade (nao e necessario para a nota conforme o edital).

## Antes de entregar

- [x] Testar o circuito breaker e as retentativas do LLM.
- [x] Confirmar o modo simulado sem chave de API.
- [x] Confirmar que a chave da API esta fora do codigo e nao foi enviada ao GitHub (`.env` esta no `.gitignore`).
- [ ] Clonar o repositorio em uma pasta limpa e seguir o README do inicio ao fim (rodar `docker compose up --build` numa maquina com Docker).
