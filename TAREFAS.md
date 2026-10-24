# TAREFAS - Trabalho C2.A2 (RAG Distribuido)

## Nucleo obrigatorio

- [x] **1. Persistencia dos documentos** - `servicos/ingestao/worker.py` grava o indice em JSON.
- [x] **2. Busca por similaridade** - `servicos/recuperacao/app.py` calcula TF-IDF e similaridade do cosseno.
- [ ] **3. Circuit breaker no LLM** - `servicos/geracao/app.py` ainda precisa envolver `gerar(...)` com `disjuntor.chamar(...)` e devolver 503 quando o circuito estiver aberto.
- [x] **4. Mensageria com Redis** - `POST /indexar` publica uma mensagem; `servicos/ingestao/worker.py` consome a fila e persiste os documentos.
- [ ] **5. Fluxo completo validado** - a arquitetura esta montada, mas precisa ser executada e testada ponta a ponta.
- [ ] **6. README final com diagrama e execucao do zero** - este README documenta a arquitetura atual; falta validar o procedimento em uma maquina limpa.

## Extensoes opcionais

- [ ] Citar quais documentos embasaram as respostas finais.
- [ ] Avaliacao automatica simples da qualidade da resposta.
- [ ] Trocar TF-IDF por embeddings de verdade (nao e necessario para a nota conforme o edital).

## Antes de entregar

- [ ] Testar o circuito breaker e as retentativas do LLM.
- [ ] Confirmar o modo simulado sem chave de API.
- [ ] Confirmar que a chave da API esta fora do codigo e nao foi enviada ao GitHub.
- [ ] Clonar o repositorio em uma pasta limpa e seguir o README do inicio ao fim.