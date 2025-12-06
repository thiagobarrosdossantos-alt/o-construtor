# O Construtor - Dockerfile
# Multi-stage build para otimizar tamanho da imagem

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instala dependências de sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Instala apenas runtime essencials
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p logs data

# SECURITY: Cria usuário não-root para rodar aplicação
# UID/GID 1000 é padrão para primeiro usuário em sistemas Linux
RUN groupadd -r appuser -g 1000 && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# SECURITY: Muda para usuário não-root
USER appuser

# Expõe portas
EXPOSE 8000 8501

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão (pode ser sobrescrito no docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
