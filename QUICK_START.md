# 🚀 Quick Start - O Construtor v2.0

## Instalação Rápida

### Opção 1: Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/o-construtor.git
cd o-construtor

# 2. Configure o .env
cp .env.example .env
# Edite .env e adicione suas chaves de API

# 3. Inicie os serviços
docker-compose up -d

# 4. Acesse
# API: http://localhost:8000
# Interface: http://localhost:8501
# Grafana: http://localhost:3000
```

### Opção 2: Local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/o-construtor.git
cd o-construtor

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
# Edite .env e adicione suas chaves

# 5. Inicie API
uvicorn api.main:app --reload

# 6. Inicie Interface (em outro terminal)
streamlit run app_advanced.py
```

## Configuração de API Keys

### 1. Anthropic (Claude)
- Acesse: https://console.anthropic.com/
- Gere uma API key
- Adicione no .env: `ANTHROPIC_API_KEY=sk-ant-...`

### 2. Google AI (Gemini)
- Acesse: https://aistudio.google.com/apikey
- Crie uma API key
- Adicione no .env: `GOOGLE_API_KEY=AIza...`

### 3. GitHub (Opcional - para automações)
- Acesse: https://github.com/settings/tokens
- Crie token com permissões: `repo`, `workflow`
- Adicione no .env: `GITHUB_TOKEN=ghp_...`

## Primeiros Passos

### 1. Criar uma Tarefa via API

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implementar nova feature",
    "description": "Adicionar autenticação de usuários",
    "task_type": "feature",
    "priority": "high"
  }'
```

### 2. Listar Agentes

```bash
curl http://localhost:8000/agents
```

### 3. Usar a Interface Web

1. Abra http://localhost:8501
2. Navegue pelo Dashboard
3. Explore as diferentes páginas (Agentes, Tarefas, Workflows, Métricas)
4. Use o Chat para interagir com o sistema

## Workflows Predefinidos

### Implementar Feature
```python
POST /workflows
{
  "name": "Implementar Feature",
  "steps": [
    {"agent": "architect", "action": "design"},
    {"agent": "developer", "action": "implement"},
    {"agent": "reviewer", "action": "review"},
    {"agent": "tester", "action": "test"}
  ]
}
```

### Corrigir Bug
```python
POST /workflows
{
  "name": "Corrigir Bug",
  "steps": [
    {"agent": "developer", "action": "analyze"},
    {"agent": "developer", "action": "fix"},
    {"agent": "tester", "action": "validate"}
  ]
}
```

## Comandos Úteis

```bash
# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f

# Reiniciar um serviço
docker-compose restart api

# Rodar testes
pytest tests/ -v

# Lint do código
black .
isort .
ruff check .

# Build da imagem
docker build -t o-construtor .
```

## Troubleshooting

### API não inicia
- Verifique se as portas 8000 e 8501 estão disponíveis
- Confirme que as API keys estão no .env
- Veja os logs: `docker-compose logs api`

### Interface não conecta
- Certifique-se de que a API está rodando
- Verifique o URL da API no .env

### Erro de autenticação
- Verifique se suas API keys são válidas
- Confirme que as keys têm permissões necessárias

## Próximos Passos

- 📖 Leia a [Documentação Completa](README.md)
- 🤝 Veja o [Guia de Contribuição](CONTRIBUTING.md)
- 📊 Explore os [Exemplos](docs/examples/)
- 💬 Entre no [Discord](link-discord)

## Suporte

- 🐛 Issues: https://github.com/usuario/o-construtor/issues
- 💬 Discussions: https://github.com/usuario/o-construtor/discussions
- 📧 Email: suporte@o-construtor.dev
