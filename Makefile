# O Construtor - Makefile
# Comandos úteis para desenvolvimento

.PHONY: help install dev test lint format clean docker-up docker-down

help: ## Mostra esta ajuda
	@echo "O Construtor - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências
	pip install --upgrade pip
	pip install -r requirements.txt

dev: ## Inicia ambiente de desenvolvimento
	@echo "Iniciando API..."
	@uvicorn api.main:app --reload --port 8000 &
	@echo "Iniciando Interface..."
	@streamlit run app_advanced.py --server.port 8501

test: ## Roda todos os testes
	pytest tests/ -v --cov=. --cov-report=html

test-unit: ## Roda apenas testes unitários
	pytest tests/unit/ -v

test-integration: ## Roda apenas testes de integração
	pytest tests/integration/ -v

lint: ## Verifica qualidade do código
	black --check .
	isort --check-only .
	ruff check .
	mypy . --ignore-missing-imports

format: ## Formata o código
	black .
	isort .
	ruff check --fix .

clean: ## Limpa arquivos temporários
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache

docker-build: ## Build da imagem Docker
	docker-compose build

docker-up: ## Inicia todos os serviços
	docker-compose up -d

docker-down: ## Para todos os serviços
	docker-compose down

docker-logs: ## Mostra logs dos serviços
	docker-compose logs -f

docker-restart: ## Reinicia serviços
	docker-compose restart

docker-clean: ## Remove containers e volumes
	docker-compose down -v
	docker system prune -f

api: ## Inicia apenas a API
	uvicorn api.main:app --reload --port 8000

web: ## Inicia apenas a interface
	streamlit run app_advanced.py --server.port 8501

redis: ## Inicia Redis local
	docker run -d -p 6379:6379 redis:7-alpine

docs: ## Gera documentação da API
	@echo "Documentação disponível em http://localhost:8000/docs"

db-migrate: ## Roda migrations do banco
	@echo "Migrations não implementadas ainda"

db-seed: ## Popula banco com dados de exemplo
	@echo "Seed não implementado ainda"

security-check: ## Verifica vulnerabilidades
	pip-audit
	bandit -r .

requirements: ## Atualiza requirements.txt
	pip freeze > requirements.txt

init: install docker-up ## Setup inicial do projeto
	@echo "Setup completo!"
	@echo "API: http://localhost:8000"
	@echo "Interface: http://localhost:8501"
	@echo "Grafana: http://localhost:3000"

ci: lint test ## Roda verificações de CI localmente
	@echo "CI checks passed!"
