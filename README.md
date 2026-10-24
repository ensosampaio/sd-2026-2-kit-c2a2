# RAG Distribuído em Microsserviços — C2.A2

Disciplina: Sistemas Distribuídos e Computação em Nuvem · FAESA · 2026/2  
Entrega indicada no edital: 29/10/2026

Projeto acadêmico de perguntas e respostas baseado em documentos próprios. A aplicação foi dividida em três serviços independentes: ingestão, recuperação e geração.

> **Estado do projeto:** foi implementada a comunicação REST entre os serviços e uma fila Redis na ingestão. A implementação ainda precisa ser executada e validada no ambiente de desenvolvimento. O circuit breaker e as retentativas na chamada ao LLM continuam pendentes.

## Arquitetura atual

```mermaid
flowchart LR
    U[Cliente] -->|REST: POST /indexar| I[API de ingestão :8001]
    I -->|Publica mensagem| Q[(Fila Redis)]
    Q -->|Consome mensagem| W[Worker de ingestão]
    W --> D[(indice.json)]
    R[Serviço de recuperação :8002] -->|REST: GET /indice| I
    R -->|Calcula similaridade| D
    G[Serviço de geração :8003] -->|REST: POST /buscar| R
    U -->|REST: POST /perguntar| G
    G --> L[Cliente LLM: API ou modo simulado]