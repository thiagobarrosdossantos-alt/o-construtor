# 🔗 Guia de Integração com GitHub

**O Construtor v2.0** pode trabalhar com qualquer repositório GitHub para:
- Clonar e analisar código
- Dar continuidade a projetos
- Melhorar aplicativos existentes
- Criar Pull Requests
- Revisar código automaticamente
- Responder a Issues

---

## 🎯 CAPACIDADES DISPONÍVEIS

### 1. **GitHub Client** (Integração com GitHub API)

**Funcionalidades:**
- ✅ Buscar informações de repositórios
- ✅ Listar e analisar Pull Requests
- ✅ Criar e comentar em Issues
- ✅ Criar Pull Requests automaticamente
- ✅ Fazer code review automático
- ✅ Gerenciar branches
- ✅ Ler arquivos remotos
- ✅ Obter histórico de commits

### 2. **Claude Code** (Trabalha com Git)

**Funcionalidades:**
- ✅ Clonar repositórios
- ✅ Analisar codebase completo
- ✅ Implementar features
- ✅ Corrigir bugs
- ✅ Refatorar código
- ✅ Criar commits
- ✅ Push para remote

### 3. **Multi-AI Review**

**Funcionalidades:**
- ✅ Architect (Claude Opus 4.5) - Analisa arquitetura
- ✅ Developer (Claude + Gemini) - Implementa mudanças
- ✅ Reviewer (Gemini 3 Pro) - Revisa qualidade
- ✅ Security (Gemini 3 Pro) - Analisa segurança
- ✅ Tester (Gemini 2.5 Flash) - Valida testes

---

## 🚀 EXEMPLOS PRÁTICOS

### Exemplo 1: Clonar e Analisar Repositório

```python
import asyncio
from integrations.github_client import GitHubClient
from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent

async def analyze_github_repo():
    # 1. Configurar cliente GitHub
    github = GitHubClient(repo="facebook/react")
    await github.initialize()

    # 2. Obter informações do repo
    repo_info = await github.get_repository_info()
    print(f"Analisando: {repo_info['name']}")
    print(f"Descrição: {repo_info['description']}")

    # 3. Clonar localmente (via git)
    import subprocess
    subprocess.run([
        "git", "clone",
        "https://github.com/facebook/react.git",
        "/tmp/react"
    ])

    # 4. Analisar com Architect
    architect = ArchitectAgent()
    analysis = await architect.analyze_codebase("/tmp/react")
    print(f"Análise: {analysis}")
```

### Exemplo 2: Melhorar Aplicativo Existente

```python
async def improve_existing_app(repo_url: str, improvement: str):
    """
    Melhora um aplicativo existente do GitHub

    Args:
        repo_url: URL do repositório (ex: "https://github.com/user/app")
        improvement: Descrição da melhoria (ex: "Adicionar autenticação JWT")
    """
    # 1. Clonar o repositório
    import subprocess
    import os

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = f"/tmp/{repo_name}"

    subprocess.run(["git", "clone", repo_url, clone_path])
    os.chdir(clone_path)

    # 2. Orquestrador analisa o projeto
    from core.orchestrator import Orchestrator
    orchestrator = Orchestrator()
    await orchestrator.initialize()

    # 3. Criar tarefa de melhoria
    task = await orchestrator.create_task({
        "title": f"Melhorar: {improvement}",
        "description": f"""
        Repositório: {repo_url}
        Path local: {clone_path}

        Tarefa:
        1. Analisar código existente
        2. Implementar: {improvement}
        3. Criar testes
        4. Documentar mudanças
        5. Criar Pull Request
        """,
        "task_type": "feature",
        "priority": "high"
    })

    # 4. Executar workflow completo
    workflow = {
        "steps": [
            {"agent": "architect", "action": "analyze_and_design"},
            {"agent": "developer", "action": "implement"},
            {"agent": "tester", "action": "test"},
            {"agent": "reviewer", "action": "review"},
            {"agent": "devops", "action": "prepare_pr"}
        ]
    }

    result = await orchestrator.execute_workflow(workflow, task)
    return result
```

### Exemplo 3: Continuar Projeto Incompleto

```python
async def continue_incomplete_project(repo_url: str):
    """
    Analisa um projeto incompleto e continua o desenvolvimento
    """
    # 1. Clonar
    repo_name = repo_url.split("/")[-1]
    subprocess.run(["git", "clone", repo_url, f"/tmp/{repo_name}"])

    # 2. Architect analisa o que está faltando
    architect = ArchitectAgent()
    analysis = await architect.analyze_project_status(f"/tmp/{repo_name}")

    print("📊 Status do Projeto:")
    print(f"- Completo: {analysis['completion_percentage']}%")
    print(f"- Faltando: {', '.join(analysis['missing_features'])}")
    print(f"- Bugs encontrados: {len(analysis['bugs'])}")

    # 3. Criar tasks para cada item faltante
    tasks = []
    for feature in analysis['missing_features']:
        task = await orchestrator.create_task({
            "title": f"Implementar: {feature}",
            "description": f"Feature faltante identificada: {feature}",
            "task_type": "feature"
        })
        tasks.append(task)

    # 4. Executar todas as tasks
    for task in tasks:
        await orchestrator.assign_and_execute(task)
```

### Exemplo 4: Review Automático de Pull Requests

```python
async def auto_review_pr(repo: str, pr_number: int):
    """
    Faz review automático de um PR com múltiplos agentes
    """
    github = GitHubClient(repo=repo)
    await github.initialize()

    # 1. Obter PR
    pr = await github.get_pull_request(pr_number)
    print(f"Reviewing PR #{pr_number}: {pr.title}")

    # 2. Obter arquivos modificados
    files = await github.get_pr_files(pr_number)

    # 3. Review por múltiplos agentes
    reviews = {}

    # Security Review
    from agents.security import SecurityAgent
    security = SecurityAgent()
    reviews['security'] = await security.review_code(files)

    # Code Quality Review
    from agents.reviewer import ReviewerAgent
    reviewer = ReviewerAgent()
    reviews['quality'] = await reviewer.review_code(files)

    # Architecture Review
    from agents.architect import ArchitectAgent
    architect = ArchitectAgent()
    reviews['architecture'] = await architect.review_architecture(files)

    # 4. Consolidar reviews
    final_review = consolidate_reviews(reviews)

    # 5. Postar no GitHub
    await github.post_review(
        pr_number=pr_number,
        body=final_review['body'],
        decision=final_review['decision'],
        comments=final_review['comments']
    )

    return final_review
```

---

## 📋 WORKFLOWS PREDEFINIDOS

### Workflow 1: "Analisar Repositório"

```json
{
  "name": "Analisar Repositório GitHub",
  "steps": [
    {
      "agent": "architect",
      "action": "analyze_codebase",
      "description": "Analisa estrutura e arquitetura"
    },
    {
      "agent": "security",
      "action": "scan_vulnerabilities",
      "description": "Busca vulnerabilidades"
    },
    {
      "agent": "optimizer",
      "action": "identify_improvements",
      "description": "Identifica melhorias de performance"
    }
  ]
}
```

### Workflow 2: "Implementar Feature em Repo Existente"

```json
{
  "name": "Implementar Feature",
  "steps": [
    {
      "agent": "architect",
      "action": "design_solution",
      "description": "Projeta a solução"
    },
    {
      "agent": "developer",
      "action": "implement",
      "description": "Implementa a feature"
    },
    {
      "agent": "tester",
      "action": "create_tests",
      "description": "Cria testes"
    },
    {
      "agent": "reviewer",
      "action": "review",
      "description": "Revisa o código"
    },
    {
      "agent": "devops",
      "action": "create_pr",
      "description": "Cria Pull Request"
    }
  ]
}
```

### Workflow 3: "Refatoração Completa"

```json
{
  "name": "Refatorar Código",
  "steps": [
    {
      "agent": "architect",
      "action": "analyze_current_state",
      "description": "Analisa código atual"
    },
    {
      "agent": "optimizer",
      "action": "suggest_refactoring",
      "description": "Sugere melhorias"
    },
    {
      "agent": "developer",
      "action": "refactor",
      "description": "Refatora o código"
    },
    {
      "agent": "tester",
      "action": "regression_test",
      "description": "Testa regressão"
    }
  ]
}
```

---

## 🎯 CASOS DE USO REAIS

### Caso 1: Melhorar App Open Source

**Cenário:** Você encontrou um app open source no GitHub que quer melhorar.

**Como usar O Construtor:**

1. **Configure o repositório:**
   ```bash
   export GITHUB_REPOSITORY="owner/repo-name"
   export GITHUB_TOKEN="seu_token"
   ```

2. **Use a interface web:**
   - Acesse http://localhost:8501
   - Vá em "Workflows"
   - Selecione "Melhorar Repositório Existente"
   - Cole a URL do repo
   - Descreva as melhorias desejadas

3. **O sistema irá:**
   - Clonar o repositório
   - Analisar o código
   - Implementar melhorias
   - Criar testes
   - Gerar Pull Request

### Caso 2: Continuar Projeto Abandonado

**Cenário:** Projeto interessante mas abandonado há meses.

**Passos:**

1. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Continuar projeto XYZ",
       "description": "Repo: https://github.com/user/abandoned-project",
       "task_type": "maintenance",
       "priority": "medium",
       "metadata": {
         "repo_url": "https://github.com/user/abandoned-project",
         "action": "continue_development"
       }
     }'
   ```

2. **O sistema irá:**
   - Analisar o estado atual
   - Identificar pendências
   - Listar bugs
   - Sugerir próximos passos
   - Implementar correções

### Caso 3: Code Review Automático

**Cenário:** Você tem um PR grande e quer review detalhado.

**Configuração GitHub Actions:**

```yaml
# .github/workflows/o-construtor-review.yml
name: O Construtor Auto Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Run O Construtor Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          python -m o_construtor.review_pr \
            --repo ${{ github.repository }} \
            --pr ${{ github.event.pull_request.number }}
```

---

## 💡 DICAS IMPORTANTES

### 1. **Permissões do Token GitHub**

Seu token precisa destas permissões:
- ✅ `repo` - Acesso a repositórios
- ✅ `workflow` - Modificar workflows
- ✅ `pull_request` - Gerenciar PRs
- ✅ `write:discussion` - Comentar

### 2. **Repositórios Privados**

O sistema funciona com repos privados! Apenas configure:
```bash
export GITHUB_TOKEN="seu_token_com_acesso_ao_repo_privado"
```

### 3. **Limites de Rate**

GitHub API tem limites:
- **5,000 requests/hora** com autenticação
- **60 requests/hora** sem autenticação

O sistema gerencia isso automaticamente.

### 4. **Tamanho de Repositórios**

Para repos muito grandes (>1GB):
- Use `--depth 1` para clonar shallow
- Ou trabalhe apenas com arquivos específicos via API

---

## 🔧 CONFIGURAÇÃO RÁPIDA

### 1. Adicione no `.env`:

```bash
# GitHub
GITHUB_TOKEN=ghp_seu_token_aqui
GITHUB_REPOSITORY=owner/repo  # opcional, pode especificar depois
```

### 2. Teste a conexão:

```python
from integrations.github_client import GitHubClient

async def test():
    client = GitHubClient()
    await client.initialize()
    user = await client.get_authenticated_user()
    print(f"Conectado como: {user['login']}")

asyncio.run(test())
```

### 3. Use via interface web:

http://localhost:8501 → **Workflows** → **Trabalhar com Repositório GitHub**

---

## 📊 EXEMPLO COMPLETO

### Script para Melhorar Qualquer Repositório:

```python
#!/usr/bin/env python3
"""
improve_github_repo.py
Melhora qualquer repositório do GitHub automaticamente
"""

import asyncio
import sys
from core.orchestrator import Orchestrator
from integrations.github_client import GitHubClient

async def improve_repository(repo_url: str, improvements: list[str]):
    """
    Melhora um repositório GitHub

    Args:
        repo_url: URL do repositório
        improvements: Lista de melhorias a fazer
    """
    print(f"🚀 Iniciando melhorias em: {repo_url}")

    # 1. Inicializar sistema
    orchestrator = Orchestrator()
    await orchestrator.initialize()

    # 2. Clonar repositório
    import subprocess
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = f"./{repo_name}"

    print(f"📥 Clonando repositório...")
    subprocess.run(["git", "clone", repo_url, clone_path], check=True)

    # 3. Criar tasks para cada melhoria
    print(f"📋 Criando {len(improvements)} tarefas...")
    for improvement in improvements:
        task = await orchestrator.create_task({
            "title": improvement,
            "description": f"Repositório: {clone_path}\nMelhoria: {improvement}",
            "task_type": "feature",
            "priority": "high",
            "metadata": {
                "repo_path": clone_path,
                "repo_url": repo_url
            }
        })

        # 4. Executar workflow
        print(f"⚙️ Executando: {improvement}")
        result = await orchestrator.execute_workflow({
            "steps": [
                {"agent": "architect", "action": "analyze"},
                {"agent": "developer", "action": "implement"},
                {"agent": "tester", "action": "test"},
                {"agent": "reviewer", "action": "review"}
            ]
        }, task)

        print(f"✅ Concluído: {improvement}")
        print(f"   Resultado: {result['status']}")

    print("🎉 Todas as melhorias foram aplicadas!")
    print(f"📁 Código atualizado em: {clone_path}")
    print("💡 Próximos passos:")
    print("   1. Revise as mudanças: cd", clone_path, "&& git diff")
    print("   2. Faça commit: git add . && git commit -m 'Melhorias do O Construtor'")
    print("   3. Crie PR: git push origin feature/improvements")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python improve_github_repo.py <repo_url> [melhorias...]")
        print()
        print("Exemplo:")
        print("  python improve_github_repo.py \\")
        print("    https://github.com/user/app \\")
        print("    'Adicionar autenticação JWT' \\")
        print("    'Melhorar performance do banco de dados' \\")
        print("    'Adicionar testes de integração'")
        sys.exit(1)

    repo_url = sys.argv[1]
    improvements = sys.argv[2:] if len(sys.argv) > 2 else [
        "Melhorar documentação",
        "Adicionar testes",
        "Otimizar performance"
    ]

    asyncio.run(improve_repository(repo_url, improvements))
```

### Como usar:

```bash
# Exemplo 1: Melhorias padrão
python improve_github_repo.py https://github.com/user/my-app

# Exemplo 2: Melhorias específicas
python improve_github_repo.py https://github.com/user/my-app \
  "Adicionar Docker" \
  "Implementar CI/CD" \
  "Melhorar segurança"
```

---

## 🎯 RESUMO

**SIM! O Construtor v2.0 pode:**

✅ **Clonar** qualquer repositório GitHub (público ou privado)
✅ **Analisar** o código completo com múltiplos agentes IA
✅ **Continuar** projetos abandonados ou incompletos
✅ **Melhorar** aplicativos existentes
✅ **Implementar** novas features
✅ **Corrigir** bugs automaticamente
✅ **Refatorar** código legado
✅ **Criar** Pull Requests
✅ **Revisar** PRs automaticamente com multi-AI
✅ **Gerenciar** Issues e comentários

**Tudo integrado, automatizado e coordenado por múltiplos agentes IA!** 🚀

---

**Próximo passo:** Quer que eu crie um exemplo prático trabalhando com um repositório específico?
