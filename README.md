# 🏗️ O Construtor v2.0

**O Construtor** é uma plataforma de Engenharia de Software Autônoma que orquestra múltiplos agentes de Inteligência Artificial para criar, revisar e deployar aplicações de forma completamente autônoma.

> *"Não apenas escrevemos código, nós construímos o futuro."*

---

## 🎯 Visão

Criar um ecossistema onde múltiplas IAs trabalham em equipe sincronizada, cada uma com sua especialidade, para desenvolver software de alta qualidade sem intervenção humana.

---

## 🤖 A Equipe de Agentes

### Agentes Principais

| Agente | Modelo | Especialidade | Responsabilidades |
|--------|--------|---------------|-------------------|
| 🏛️ **Arquiteto** | Claude Opus 4.5 | Design de Sistemas | Arquitetura, SOLID, Design Patterns, APIs |
| 👨‍💻 **Desenvolvedor** | Claude Code + Gemini Code Assist | Implementação | Coding, Refactoring, Bug Fixing |
| 🔍 **Revisor** | Gemini 3 Pro Preview | Code Review | Qualidade, Performance, Segurança |
| 🧪 **Tester** | Gemini 2.5 Flash | Testes | Unit, Integration, E2E Tests |
| 🚀 **Jules (DevOps)** | Gemini 2.5 Pro | Infraestrutura | CI/CD, Docker, Kubernetes, Deploy |
| 🔐 **Segurança** | Gemini 3 Pro Preview | Vulnerabilidades | OWASP, Auth, Secrets |
| ⚡ **Otimizador** | Gemini 3 Pro Preview | Performance | Big O, Profiling, Caching |

### Estratégia de Modelos

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAPEAMENTO ESTRATÉGICO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TAREFAS DE RACIOCÍNIO PROFUNDO                                │
│  ├── Arquitetura de Sistemas    → Claude Opus 4.5              │
│  ├── Design de APIs             → Claude Opus 4.5              │
│  └── Decisões Arquiteturais     → Claude Opus 4.5              │
│                                                                 │
│  TAREFAS DE ANÁLISE AVANÇADA                                   │
│  ├── Performance Analysis       → Gemini 3 Pro Preview         │
│  ├── Security Analysis          → Gemini 3 Pro Preview         │
│  ├── Code Review Profundo       → Gemini 3 Pro Preview         │
│  └── Otimização de Algoritmos   → Gemini 3 Pro Preview         │
│                                                                 │
│  TAREFAS DE IMPLEMENTAÇÃO                                      │
│  ├── Coding Autônomo            → Claude Code (líder)          │
│  ├── Autocomplete/Sugestões     → Gemini Code Assist           │
│  └── Refactoring                → Claude Code + Gemini 3 Pro   │
│                                                                 │
│  TAREFAS DE ALTA VELOCIDADE                                    │
│  ├── Geração de Testes          → Gemini 2.5 Flash             │
│  ├── Chat Interativo            → Gemini 2.0 Flash             │
│  └── Validações Rápidas         → Gemini 2.5 Flash             │
│                                                                 │
│  TAREFAS DE DEVOPS                                             │
│  ├── CI/CD Configuration        → Gemini 2.5 Pro               │
│  ├── Docker/Kubernetes          → Gemini 2.5 Pro               │
│  └── Infrastructure as Code     → Gemini 2.5 Pro               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        O CONSTRUTOR v2.0 - ECOSSISTEMA                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    🧠 CÉREBRO CENTRAL (Orquestrador)                │    │
│  │  • Coordena todos os agentes                                        │    │
│  │  • Gerencia fluxos de trabalho                                      │    │
│  │  • Distribui tarefas por especialidade                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ↕                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    📡 HUB DE COMUNICAÇÃO                            │    │
│  │  • Event Bus (Pub/Sub entre agentes)                                │    │
│  │  • Memory Store (Contexto compartilhado)                            │    │
│  │  • Task Queue (Fila de tarefas prioritárias)                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       ↙         ↓          ↓          ↓          ↓          ↘              │
│  ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐   │
│  │Arquitet││Desenvol││Revisor ││ Tester ││ DevOps ││Seguranç││Otimizad│   │
│  │  🏛️   ││  👨‍💻  ││  🔍   ││  🧪   ││  🚀   ││  🔐   ││  ⚡   │   │
│  └────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    🔧 CAMADA DE INTEGRAÇÃO                          │    │
│  │  • Claude Code CLI                                                   │    │
│  │  • Gemini Code Assist                                               │    │
│  │  • GitHub API                                                        │    │
│  │  • Vertex AI                                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura do Projeto

```
o-construtor/
├── 📁 config/              # Configurações centralizadas
│   ├── settings.py         # Settings globais
│   ├── models.py           # Configuração estratégica de modelos
│   └── prompts/            # System prompts dos agentes
│
├── 📁 core/                # Núcleo do sistema
│   ├── orchestrator.py     # Cérebro central
│   ├── event_bus.py        # Comunicação entre agentes
│   ├── memory_store.py     # Memória compartilhada
│   └── task_queue.py       # Fila de tarefas
│
├── 📁 agents/              # Agentes especializados
│   ├── base_agent.py       # Classe base
│   ├── architect.py        # Agente Arquiteto
│   ├── developer.py        # Agente Desenvolvedor
│   ├── reviewer.py         # Agente Revisor
│   ├── tester.py           # Agente Tester
│   ├── devops.py           # Agente DevOps (Jules)
│   ├── security.py         # Agente Segurança
│   └── optimizer.py        # Agente Otimizador
│
├── 📁 integrations/        # Integrações externas
│   ├── claude_code_client.py      # Claude Code CLI
│   ├── gemini_code_assist.py      # Gemini Code Assist
│   ├── vertex_ai_client.py        # Vertex AI (Claude + Gemini)
│   └── github_client.py           # GitHub API
│
├── 📁 api/                 # API Server (FastAPI)
│   └── routes/             # Endpoints
│
├── 📁 .github/             # GitHub Actions
│   ├── scripts/            # Workers de automação
│   └── workflows/          # Workflows CI/CD
│
├── 📄 app.py               # Interface Streamlit
├── 📄 requirements.txt     # Dependências
└── 📄 README.md            # Este arquivo
```

---

## 🚀 Como Iniciar

### 1. Clone o repositório
```bash
git clone https://github.com/usuario/o-construtor.git
cd o-construtor
```

### 2. Configure o ambiente
```bash
# Crie arquivo .env
cat > .env << EOF
# Anthropic (Claude) - API Direta
ANTHROPIC_API_KEY=sua_chave_anthropic

# Google AI (Gemini)
GOOGLE_API_KEY=sua_chave_google
GCP_PROJECT_ID=seu_projeto_gcp

# GitHub
GITHUB_TOKEN=seu_token_github

# Supabase (opcional)
SUPABASE_URL=sua_url_supabase
SUPABASE_KEY=sua_chave_supabase
EOF
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute
```bash
# Interface Streamlit
streamlit run app.py

# Ou API Server (quando disponível)
uvicorn api.main:app --reload
```

---

## 🔧 Fluxos de Trabalho Automatizados

### PR Review Automático
Quando um Pull Request é aberto, três agentes analisam em paralelo:

1. **Claude Opus 4.5**: Arquitetura, SOLID, Design Patterns
2. **Gemini 3 Pro Preview**: Performance, Big O, Segurança
3. **Jules (Gemini 2.5 Pro)**: CI/CD, Docker, Testes

### Implementação de Feature
```
Issue Criada
    ↓
🏛️ Arquiteto (design)
    ↓
👨‍💻 Desenvolvedor (código)
    ↓
🔍 Revisor (review)
    ↓
🧪 Tester (testes)
    ↓
🔐 Segurança (análise)
    ↓
🚀 DevOps (deploy)
    ↓
Issue Fechada ✅
```

---

## 🔌 Colaboração Claude Code + Gemini Code Assist

O sistema usa **duas ferramentas de código juntas** para máxima eficiência:

| Ferramenta | Papel | Uso |
|------------|-------|-----|
| **Claude Code** | Líder | Implementação autônoma, execução de comandos, edição de arquivos |
| **Gemini Code Assist** | Assistente | Autocomplete, sugestões em tempo real, validação |

### Workflow de Colaboração:
1. Claude Code recebe a tarefa e planeja
2. Gemini Code Assist sugere snippets e patterns
3. Claude Code implementa a solução
4. Gemini Code Assist valida e sugere melhorias
5. Claude Code finaliza o código

---

## 📊 Modelos Disponíveis

| Modelo | Provider | Melhor Para |
|--------|----------|-------------|
| `claude-opus-4-5-20251101` | Anthropic (API Direta) | Arquitetura, raciocínio profundo |
| `claude-sonnet-4-5-20250929` | Anthropic (API Direta) | Implementação, código geral |
| `gemini-3-pro-preview` | Google (Vertex) | Performance, segurança, análise |
| `gemini-2.5-pro` | Google (Vertex) | DevOps, documentação, review |
| `gemini-2.5-flash-preview-05-20` | Google (Vertex) | Testes, alta velocidade |
| `gemini-2.0-flash-exp` | Google (AI Studio) | Chat, baixa latência |

---

## 🛠️ Tecnologias

- **Interface:** Streamlit
- **API:** FastAPI
- **AI Providers:** Anthropic (Claude API Direta), Vertex AI (Gemini), Google AI Studio
- **IDE Integration:** Claude Code CLI, Gemini Code Assist
- **Database:** Supabase (planejado)
- **Cache:** Redis (planejado)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana (planejado)

---

## 🗺️ Roadmap

### v2.0 (Atual)
- [x] Orquestrador Central
- [x] Sistema de Memória Compartilhada
- [x] Event Bus para comunicação
- [x] 7 Agentes Especializados
- [x] Integração Claude Code + Gemini Code Assist
- [x] Estratégia de modelos otimizada

### v2.1 (Próximo)
- [ ] API Server completo (FastAPI)
- [ ] WebSocket para streaming
- [ ] Integração Supabase
- [ ] Dashboard de métricas

### v3.0 (Futuro)
- [ ] Execução 100% autônoma
- [ ] Fine-tuning de modelos
- [ ] Multi-repositório
- [ ] Self-healing (correção automática)

---

## 📄 Licença

MIT License - Use, modifique e distribua livremente.

---

*Versão 2.0 - O Construtor - Sistema Autônomo de Engenharia de Software*
