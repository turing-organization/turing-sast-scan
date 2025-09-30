# Usar uma imagem base do Python
FROM python:3.12-alpine

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos de requisitos para o diretório de trabalho
COPY requirements.txt .

# Instale as dependências necessárias
RUN apk add --no-cache \
    bash \
    curl \
    git \
    openjdk17 \
    unzip \
    wget \
    && python -m ensurepip \
    && pip install --upgrade pip

RUN curl -fsSL https://raw.githubusercontent.com/ZupIT/horusec/main/deployments/scripts/install.sh | bash -s latest

# Instalar PyArmor versão 8
RUN pip install pyarmor==8.5.12

# Copie o restante do código da aplicação para o diretório de trabalho
COPY . .

# Ofuscar os arquivos Python usando PyArmor 8
RUN pyarmor gen -O . app.py common

# Definir a porta em que a aplicação irá rodar
EXPOSE 7070

# Defina o comando para rodar a aplicação
CMD ["python", "app.py"]
