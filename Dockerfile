FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY servicos ./servicos

# O comando de cada servico e definido no docker-compose.yml
CMD ["uvicorn", "servicos.geracao.app:app", "--host", "0.0.0.0", "--port", "8003"]
