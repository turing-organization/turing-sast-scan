# Stage 1: Pegar o binário do Horusec
FROM horuszup/horusec-cli:v2.9.0-beta.3 AS horusec

# Stage 2: Build da aplicação
FROM python:3.11-slim

# Instalar git (necessário para clonar repositórios)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copiar o binário do Horusec da stage anterior
COPY --from=horusec /usr/local/bin/horusec /usr/local/bin/horusec

# Setar diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Expor porta
EXPOSE 7070

# Rodar aplicação
CMD ["python3", "app.py"]
