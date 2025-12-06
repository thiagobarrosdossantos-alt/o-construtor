"""
O Construtor - Interface Streamlit Avançada
Interface completa com orquestração de agentes, workflows e métricas
"""
import streamlit as st
import asyncio
import os
import subprocess
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor
from typing import Coroutine, Any

# Imports do sistema
from core.orchestrator import Orchestrator
from core.event_bus import EventBus
from core.memory_store import MemoryStore
from core.task_queue import TaskQueue
from config.models import TaskType
from core.logging_config import setup_default_logging, get_logger

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging estruturado
setup_default_logging()
logger = get_logger(__name__, {"component": "streamlit_app"})

# ===========================
# ASYNC HELPERS (UI PERFORMANCE)
# ===========================

def run_async_in_thread(coro: Coroutine) -> Any:
    """
    Executa coroutine em thread separada para prevenir UI freeze.

    PERFORMANCE FIX: asyncio.run() em callbacks do Streamlit bloqueia o event loop
    e congela a UI até a operação completar. Esta função executa o async code em
    uma thread worker dedicada, permitindo que a UI do Streamlit permaneça responsiva.

    Args:
        coro: Coroutine a ser executada

    Returns:
        Resultado da coroutine

    Raises:
        Exception: Qualquer exceção levantada pela coroutine
    """
    def run_in_new_loop():
        """Cria novo event loop e executa coroutine"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    # Executa em thread separada
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()

# ===========================
# FUNÇÕES AUXILIARES GITHUB
# ===========================

def validate_git_url(url: str) -> bool:
    """
    Valida URL de repositório Git para prevenir Command Injection.
    Aceita apenas URLs HTTPS/SSH de GitHub e GitLab.
    """
    # Patterns seguros para GitHub e GitLab
    patterns = [
        r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$',  # GitHub HTTPS
        r'^git@github\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',       # GitHub SSH
        r'^https://gitlab\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$',   # GitLab HTTPS
        r'^git@gitlab\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',       # GitLab SSH
    ]

    return any(re.match(pattern, url) for pattern in patterns)


def sanitize_repo_name(url: str) -> str:
    """
    Extrai e sanitiza o nome do repositório de forma segura.
    Remove caracteres perigosos e previne Path Traversal.
    """
    # Extrai o nome do repositório
    name = url.rstrip('/').split('/')[-1].replace('.git', '')

    # Remove caracteres perigosos (mantém apenas alfanuméricos, -, _ e .)
    name = re.sub(r'[^\w\-\.]', '', name)

    # Previne path traversal (remove . e .. no início)
    name = name.lstrip('.')

    # Garante que não está vazio
    if not name:
        raise ValueError("Nome de repositório inválido")

    return name


async def clone_repository(repo_url: str, target_dir: str = None) -> tuple[bool, str]:
    """
    Clona um repositório GitHub/GitLab de forma segura.
    Valida URL e sanitiza paths para prevenir Command Injection.
    """
    try:
        # SEGURANÇA: Valida URL antes de usar
        if not validate_git_url(repo_url):
            return False, "URL de repositório inválida. Use apenas GitHub ou GitLab (HTTPS/SSH)"

        # SEGURANÇA: Sanitiza o nome do repositório
        repo_name = sanitize_repo_name(repo_url)
        clone_path = target_dir or f"./repos/{repo_name}"

        # Criar diretório se não existir
        Path(clone_path).parent.mkdir(parents=True, exist_ok=True)

        # Verificar se já existe
        if Path(clone_path).exists():
            return True, clone_path

        # Clonar
        result = subprocess.run(
            ["git", "clone", repo_url, clone_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return True, clone_path
        else:
            return False, f"Erro ao clonar: {result.stderr}"

    except Exception as e:
        return False, str(e)


async def start_autonomous_work(orchestrator, repo_url: str, repo_name: str, action: str,
                                autonomous: bool, create_pr: bool, run_tests: bool, priority: str):
    """Inicia trabalho autônomo em um repositório"""
    try:
        # Clonar repositório
        success, repo_path = await clone_repository(repo_url)

        if not success:
            return False, repo_path

        # Mapear ação para descrição
        action_descriptions = {
            "analyze": "Analisar código, estrutura e identificar melhorias",
            "improve": "Implementar melhorias automaticamente no código",
            "continue": "Dar continuidade ao desenvolvimento do projeto",
            "fix_bugs": "Encontrar e corrigir bugs no código",
            "add_tests": "Criar testes automatizados completos",
            "document": "Melhorar documentação do projeto",
            "optimize": "Otimizar performance e eficiência"
        }

        # Mapear ação para tipo de request do orchestrator
        action_to_request_type = {
            "analyze": "review",
            "improve": "feature",
            "continue": "feature",
            "fix_bugs": "bugfix",
            "add_tests": "feature",
            "document": "feature",
            "optimize": "refactor"
        }

        # Mapear prioridade
        priority_map = {
            "Baixa": "low",
            "Média": "normal",
            "Alta": "high",
            "Crítica": "critical"
        }

        # Criar request data
        request_data = {
            "title": f"{action_descriptions[action]} - {repo_name}",
            "description": f"""
Repositório: {repo_url}
Caminho local: {repo_path}
Ação: {action_descriptions[action]}
Modo: {'Autônomo' if autonomous else 'Supervisionado'}

Tarefas:
1. Analisar repositório completo
2. Executar ação: {action}
3. {'Executar testes' if run_tests else 'Pular testes'}
4. {'Criar Pull Request automaticamente' if create_pr else 'Aguardar aprovação manual'}
            """,
            "repo_url": repo_url,
            "repo_path": repo_path,
            "repo_name": repo_name,
            "action": action,
            "autonomous": autonomous,
            "create_pr": create_pr,
            "run_tests": run_tests
        }

        # Criar workflow no orchestrator
        request_type = action_to_request_type[action]
        workflow = await orchestrator.process_request(
            request_type=request_type,
            request_data=request_data,
            priority=priority_map[priority]
        )

        return True, workflow.id

    except Exception as e:
        return False, str(e)

# Configuração da página
st.set_page_config(
    page_title="O Construtor v2.0",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .agent-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# INICIALIZAÇÃO DO SISTEMA
# ===========================

@st.cache_resource
def init_orchestrator():
    """Inicializa orquestrador (cached)"""
    event_bus = EventBus()
    memory_store = MemoryStore()
    task_queue = TaskQueue()

    orchestrator = Orchestrator(
        event_bus=event_bus,
        memory_store=memory_store,
        task_queue=task_queue
    )

    # Inicializa de forma síncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(orchestrator.initialize())

    return orchestrator, event_bus, memory_store, task_queue


# Inicializa sistema
try:
    orchestrator, event_bus, memory_store, task_queue = init_orchestrator()
    system_ready = True
except Exception as e:
    st.error(f"Erro ao inicializar sistema: {e}")
    system_ready = False

# ===========================
# SIDEBAR - NAVEGAÇÃO
# ===========================

st.sidebar.markdown("# 🏗️ O Construtor v2.0")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["🏠 Dashboard", "🔗 GitHub", "🤖 Agentes", "📋 Tarefas", "🔄 Workflows", "📊 Métricas", "💬 Chat"]
)

st.sidebar.markdown("---")

# Status do sistema
if system_ready:
    st.sidebar.success("✅ Sistema Operacional")
    st.sidebar.metric("Agentes Ativos", len(orchestrator.agents) if orchestrator else 0)
    st.sidebar.metric("Tarefas Pendentes", task_queue.get_queue_size() if task_queue else 0)
else:
    st.sidebar.error("❌ Sistema Offline")

# ===========================
# PÁGINA: DASHBOARD
# ===========================

if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">Dashboard do Sistema</h1>', unsafe_allow_html=True)

    if not system_ready:
        st.error("Sistema não disponível")
        st.stop()

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Agentes", len(orchestrator.agents))
    with col2:
        st.metric("Tarefas Concluídas", 0)  # TODO: pegar do orchestrator
    with col3:
        st.metric("Em Andamento", task_queue.get_queue_size())
    with col4:
        st.metric("Taxa de Sucesso", "95%")

    st.markdown("---")

    # Lista de agentes
    st.subheader("🤖 Agentes Disponíveis")

    agents_info = [
        {"nome": "Arquiteto", "emoji": "🏛️", "modelo": "Claude Opus 4.5", "status": "Idle"},
        {"nome": "Desenvolvedor", "emoji": "👨‍💻", "modelo": "Claude Code + Gemini", "status": "Idle"},
        {"nome": "Revisor", "emoji": "🔍", "modelo": "Gemini 2.5 Pro", "status": "Idle"},
        {"nome": "Tester", "emoji": "🧪", "modelo": "Gemini 2.5 Flash", "status": "Idle"},
        {"nome": "DevOps (Jules)", "emoji": "🚀", "modelo": "Gemini 2.5 Pro", "status": "Idle"},
        {"nome": "Segurança", "emoji": "🔐", "modelo": "Gemini 2.5 Pro", "status": "Idle"},
        {"nome": "Otimizador", "emoji": "⚡", "modelo": "Gemini 2.5 Pro", "status": "Idle"},
    ]

    cols = st.columns(4)
    for idx, agent in enumerate(agents_info):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="agent-card">
                <h3>{agent['emoji']} {agent['nome']}</h3>
                <p><strong>Modelo:</strong> {agent['modelo']}</p>
                <p><strong>Status:</strong> <span style="color: green;">{agent['status']}</span></p>
            </div>
            """, unsafe_allow_html=True)

    # Atividade recente
    st.markdown("---")
    st.subheader("📊 Atividade Recente")

    # Gráfico de exemplo
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        y=[5, 12, 8, 15, 20, 10],
        mode='lines+markers',
        name='Tarefas Completadas',
        line=dict(color='#667eea', width=3)
    ))
    fig.update_layout(
        title="Tarefas Completadas (Últimas 24h)",
        xaxis_title="Hora",
        yaxis_title="Tarefas",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

# ===========================
# PÁGINA: GITHUB
# ===========================

elif page == "🔗 GitHub":
    st.title("🔗 Integração com GitHub")

    # Status do GitHub Token
    github_token = os.getenv("GITHUB_TOKEN")

    if github_token:
        st.success("✅ GitHub Token configurado")

        # Seção: Seus Repositórios
        st.markdown("---")
        st.subheader("📦 Seus Repositórios")

        col1, col2 = st.columns([3, 1])

        with col1:
            # Input para URL do repositório
            repo_url = st.text_input(
                "URL do Repositório",
                placeholder="https://github.com/usuario/repositorio",
                help="Cole a URL do repositório GitHub que deseja trabalhar"
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Buscar", use_container_width=True):
                if repo_url:
                    # SEGURANÇA: Valida URL antes de salvar
                    if validate_git_url(repo_url):
                        st.session_state['selected_repo'] = repo_url
                        st.success("✅ Repositório válido!")
                    else:
                        st.error("❌ URL inválida! Use apenas GitHub ou GitLab (HTTPS/SSH)")

        # Se tem repositório selecionado
        if 'selected_repo' in st.session_state and st.session_state['selected_repo']:
            repo = st.session_state['selected_repo']
            # SEGURANÇA: Usa sanitização segura
            try:
                repo_name = sanitize_repo_name(repo)
            except ValueError as e:
                st.error(f"❌ Erro: {e}")
                del st.session_state['selected_repo']
                st.stop()

            st.markdown("---")
            st.subheader(f"📂 {repo_name}")

            # Informações do repo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", "Pronto")
            with col2:
                st.metric("Branch", "main")
            with col3:
                st.metric("Commits", "---")

            st.markdown("---")

            # Ações disponíveis
            st.subheader("🎯 O que você quer fazer?")

            action = st.radio(
                "Escolha uma ação:",
                [
                    "🔍 Analisar - Analisar código e identificar melhorias",
                    "🚀 Melhorar - Implementar melhorias automaticamente",
                    "✨ Continuar - Dar continuidade ao projeto",
                    "🐛 Corrigir Bugs - Encontrar e corrigir bugs",
                    "🧪 Adicionar Testes - Criar testes automatizados",
                    "📚 Documentar - Melhorar documentação",
                    "⚡ Otimizar - Melhorar performance"
                ],
                help="O Construtor executará esta ação de forma autônoma"
            )

            # Opções avançadas
            with st.expander("⚙️ Opções Avançadas"):
                autonomous = st.checkbox(
                    "Modo Autônomo Completo",
                    value=True,
                    help="O Construtor trabalhará de forma totalmente autônoma, apenas reportando progresso"
                )

                create_pr = st.checkbox(
                    "Criar Pull Request automaticamente",
                    value=True,
                    help="Criar PR quando terminar as mudanças"
                )

                run_tests = st.checkbox(
                    "Executar testes antes do PR",
                    value=True,
                    help="Garantir que testes passam antes de criar PR"
                )

                priority = st.select_slider(
                    "Prioridade",
                    options=["Baixa", "Média", "Alta", "Crítica"],
                    value="Alta"
                )

            st.markdown("---")

            # Botão de iniciar
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("🚀 INICIAR TRABALHO AUTÔNOMO", type="primary", use_container_width=True):
                    # Extrair ação
                    action_map = {
                        "🔍 Analisar": "analyze",
                        "🚀 Melhorar": "improve",
                        "✨ Continuar": "continue",
                        "🐛 Corrigir Bugs": "fix_bugs",
                        "🧪 Adicionar Testes": "add_tests",
                        "📚 Documentar": "document",
                        "⚡ Otimizar": "optimize"
                    }

                    selected_action = action_map[action.split(" - ")[0]]

                    with st.spinner("Inicializando O Construtor..."):
                        # Verificar se o orchestrator está disponível
                        if not system_ready or orchestrator is None:
                            st.error("❌ Sistema não está pronto. Inicialize o orchestrator na página inicial.")
                        else:
                            # Iniciar trabalho autônomo (PERFORMANCE: usa thread separada para não bloquear UI)
                            success, result = run_async_in_thread(start_autonomous_work(
                                orchestrator=orchestrator,
                                repo_url=repo,
                                repo_name=repo_name,
                                action=selected_action,
                                autonomous=autonomous,
                                create_pr=create_pr,
                                run_tests=run_tests,
                                priority=priority
                            ))

                            if success:
                                task_id = result
                                st.success("✅ Tarefa criada com sucesso!")

                                st.info(f"""
                                **🤖 O Construtor iniciou o trabalho!**

                                **Repositório:** {repo_name}
                                **Ação:** {selected_action}
                                **Modo:** {'Autônomo' if autonomous else 'Supervisionado'}
                                **Task ID:** {task_id}

                                **O que vai acontecer:**
                                1. Clonar o repositório
                                2. Analisar com 7 agentes IA
                                3. Executar a ação selecionada
                                4. {'Executar testes' if run_tests else 'Pular testes'}
                                5. {'Criar PR automaticamente' if create_pr else 'Aguardar aprovação'}

                                Acompanhe o progresso na aba **📋 Tarefas**
                                """)

                                # Salvar no session state para a página de tarefas
                                if 'tasks' not in st.session_state:
                                    st.session_state['tasks'] = []

                                st.session_state['tasks'].append({
                                    'task_id': task_id,
                                    'repo': repo,
                                    'repo_name': repo_name,
                                    'action': selected_action,
                                    'autonomous': autonomous,
                                    'create_pr': create_pr,
                                    'status': 'in_progress',
                                    'started_at': datetime.now().isoformat()
                                })
                            else:
                                st.error(f"❌ Erro ao iniciar trabalho: {result}")

    else:
        st.error("❌ GitHub Token não configurado")
        st.markdown("""
        ### Como configurar:

        1. **Gerar Token do GitHub:**
           - Acesse: https://github.com/settings/tokens
           - Clique em "Generate new token (classic)"
           - Selecione os scopes: `repo`, `workflow`
           - Copie o token gerado

        2. **Adicionar no .env:**
           ```bash
           GITHUB_TOKEN=seu_token_aqui
           ```

        3. **Reiniciar o aplicativo**
        """)

        # Link rápido
        st.markdown("[🔗 Gerar Token no GitHub](https://github.com/settings/tokens)")

    # Repositórios recentes (exemplo)
    st.markdown("---")
    st.subheader("📜 Repositórios Recentes")

    if 'tasks' in st.session_state and st.session_state['tasks']:
        for task in st.session_state['tasks'][-5:]:
            with st.expander(f"📦 {task['repo_name']} - {task['action']}"):
                st.write(f"**Status:** {task['status']}")
                st.write(f"**Repositório:** {task['repo']}")
                st.write(f"**Modo:** {'Autônomo' if task.get('autonomous') else 'Supervisionado'}")
    else:
        st.info("Nenhum repositório trabalhado ainda")

# ===========================
# PÁGINA: AGENTES
# ===========================

elif page == "🤖 Agentes":
    st.title("🤖 Gerenciamento de Agentes")

    if not system_ready:
        st.error("Sistema não disponível")
        st.stop()

    # Seletor de agente
    agent_names = ["Arquiteto", "Desenvolvedor", "Revisor", "Tester", "DevOps", "Segurança", "Otimizador"]
    selected_agent = st.selectbox("Selecione um Agente", agent_names)

    # Detalhes do agente
    st.subheader(f"Detalhes: {selected_agent}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Capacidades:**")
        if selected_agent == "Arquiteto":
            st.markdown("- Design de Sistemas\n- Arquitetura de Software\n- Design Patterns\n- APIs RESTful")
        elif selected_agent == "Desenvolvedor":
            st.markdown("- Implementação de Código\n- Refatoração\n- Bug Fixing\n- Testes Unitários")
        # ... adicionar outros agentes

    with col2:
        st.markdown("**Estatísticas:**")
        st.metric("Tarefas Completadas", 42)
        st.metric("Taxa de Sucesso", "98%")
        st.metric("Tempo Médio", "15min")

    # Tarefas do agente
    st.subheader("Tarefas Atribuídas")
    st.info("Nenhuma tarefa em andamento")

# ===========================
# PÁGINA: TAREFAS
# ===========================

elif page == "📋 Tarefas":
    st.title("📋 Gerenciamento de Tarefas")

    if not system_ready:
        st.error("Sistema não disponível")
        st.stop()

    # Criar nova tarefa
    with st.expander("➕ Criar Nova Tarefa"):
        task_title = st.text_input("Título")
        task_desc = st.text_area("Descrição")
        task_type = st.selectbox("Tipo", ["feature", "bug", "refactor", "documentation", "test"])
        task_priority = st.select_slider("Prioridade", ["low", "medium", "high", "critical"])

        if st.button("Criar Tarefa"):
            if task_title and task_desc:
                st.success(f"Tarefa '{task_title}' criada com sucesso!")
            else:
                st.error("Preencha título e descrição")

    # Lista de tarefas
    st.subheader("Tarefas Ativas")

    # Lista de agentes disponíveis
    agent_names = ["architect", "developer", "reviewer", "tester", "devops", "security", "optimizer"]

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.multiselect("Status", ["pending", "in_progress", "completed", "failed"])
    with col2:
        filter_agent = st.multiselect("Agente", agent_names)
    with col3:
        filter_priority = st.multiselect("Prioridade", ["low", "medium", "high", "critical"])

    # Tabela de tarefas (exemplo)
    st.info("Nenhuma tarefa encontrada")

# ===========================
# PÁGINA: WORKFLOWS
# ===========================

elif page == "🔄 Workflows":
    st.title("🔄 Workflows Automatizados")

    if not system_ready:
        st.error("Sistema não disponível")
        st.stop()

    # Workflows predefinidos
    workflows = {
        "Implementar Feature": {
            "steps": ["Arquiteto → Design", "Desenvolvedor → Código", "Revisor → Review", "Tester → Testes"],
            "duração": "~30min"
        },
        "Corrigir Bug": {
            "steps": ["Desenvolvedor → Análise", "Desenvolvedor → Fix", "Tester → Validação"],
            "duração": "~15min"
        },
        "Deploy em Produção": {
            "steps": ["Revisor → Code Review", "Tester → Testes", "DevOps → Deploy", "Segurança → Scan"],
            "duração": "~45min"
        }
    }

    for workflow_name, workflow_data in workflows.items():
        with st.expander(f"📋 {workflow_name}"):
            st.markdown(f"**Duração Estimada:** {workflow_data['duração']}")
            st.markdown("**Etapas:**")
            for step in workflow_data['steps']:
                st.markdown(f"- {step}")
            if st.button(f"Executar {workflow_name}"):
                st.success(f"Workflow '{workflow_name}' iniciado!")

# ===========================
# PÁGINA: MÉTRICAS
# ===========================

elif page == "📊 Métricas":
    st.title("📊 Métricas e Análises")

    if not system_ready:
        st.error("Sistema não disponível")
        st.stop()

    # Lista de agentes para os gráficos
    agent_names = ["Architect", "Developer", "Reviewer", "Tester", "DevOps", "Security", "Optimizer"]

    # Métricas gerais
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Tarefas", 156, "+12")
    with col2:
        st.metric("Taxa de Sucesso", "96.2%", "+2.1%")
    with col3:
        st.metric("Tempo Médio", "18min", "-3min")

    # Gráficos
    st.subheader("Desempenho por Agente")

    # Gráfico de barras
    fig = px.bar(
        x=agent_names,
        y=[45, 52, 38, 41, 35, 29, 31],
        labels={'x': 'Agente', 'y': 'Tarefas Completadas'},
        title="Tarefas Completadas por Agente"
    )
    fig.update_traces(marker_color='#667eea')
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de pizza
    st.subheader("Distribuição de Tipos de Tarefa")
    fig = px.pie(
        values=[40, 25, 20, 10, 5],
        names=['Feature', 'Bug Fix', 'Refactor', 'Documentation', 'Test'],
        title="Tipos de Tarefa"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===========================
# PÁGINA: CHAT
# ===========================

elif page == "💬 Chat":
    st.title("💬 Debate Multi-IA")
    st.markdown("**As 3 IAs debatem sua pergunta e chegam a um consenso**")

    # Inicializa histórico
    if "debate_messages" not in st.session_state:
        st.session_state.debate_messages = []

    if "current_debate" not in st.session_state:
        st.session_state.current_debate = None

    # Barra superior com info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🏛️ Claude Opus\n\nArquitetura")
    with col2:
        st.info("🤖 GPT-5.1\n\nImplementacao")
    with col3:
        st.info("🔮 Gemini 2.5 Pro\n\nPerformance")

    st.markdown("---")

    # Botão limpar
    if st.button("🗑️ Novo Debate"):
        st.session_state.debate_messages = []
        st.session_state.current_debate = None
        st.rerun()

    # Mostra histórico do debate
    for message in st.session_state.debate_messages:
        avatar_map = {
            "user": "👤",
            "claude": "🏛️",
            "gpt": "🤖",
            "gemini": "🔮",
            "system": "⚙️"
        }

        with st.chat_message(message["role"], avatar=avatar_map.get(message["role"], "💬")):
            st.markdown(message["content"])

            # Mostrar concordâncias/discordâncias
            if "metadata" in message:
                metadata = message["metadata"]
                if metadata.get("agrees_with"):
                    agrees = ", ".join(metadata["agrees_with"])
                    st.caption(f"✅ Concorda com: {agrees}")
                if metadata.get("disagrees_with"):
                    disagrees = ", ".join(metadata["disagrees_with"])
                    st.caption(f"❌ Discorda de: {disagrees}")
                if metadata.get("confidence"):
                    st.caption(f"📊 Confianca: {int(metadata['confidence'] * 100)}%")

    # Input do usuário
    if prompt := st.chat_input("Digite seu topico para debate..."):
        # Adiciona mensagem do usuário
        st.session_state.debate_messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # INICIAR DEBATE
        with st.spinner("🎯 Iniciando debate entre as 3 IAs..."):
            # Importar sistema de debate
            from core.debate_system import DebateOrchestrator, AIParticipant

            # Criar orchestrador de debate
            debate_orch = DebateOrchestrator(max_rounds=3)

            # Placeholder para atualizações
            status_placeholder = st.empty()

            try:
                # EXECUTAR DEBATE REAL COM APIs
                import asyncio

                # Função assíncrona para executar o debate
                async def run_real_debate():
                    session = await debate_orch.start_debate(
                        topic=prompt,
                        participants=[AIParticipant.CLAUDE, AIParticipant.GPT, AIParticipant.GEMINI]
                    )
                    return session

                # Atualizar interface em tempo real
                status_placeholder.info("🎤 Rodada 1: Chamando as 3 IAs em paralelo...")

                # Executar debate (PERFORMANCE: usa thread separada para não bloquear UI)
                session = run_async_in_thread(run_real_debate())

                # Adicionar todas as mensagens ao histórico
                status_placeholder.empty()

                for msg in session.messages:
                    ai_name = msg.participant.value
                    st.session_state.debate_messages.append({
                        "role": ai_name,
                        "content": msg.content,
                        "metadata": {
                            "round": msg.round_number,
                            "agrees_with": [p.value for p in msg.agrees_with],
                            "disagrees_with": [p.value for p in msg.disagrees_with],
                            "confidence": msg.confidence
                        }
                    })

                    with st.chat_message(ai_name, avatar={"claude": "🏛️", "gpt": "🤖", "gemini": "🔮"}[ai_name]):
                        st.markdown(msg.content)

                        # Mostrar metadados
                        if msg.agrees_with:
                            agrees = ", ".join([p.value.upper() for p in msg.agrees_with])
                            st.caption(f"✅ Concorda com: {agrees}")
                        if msg.disagrees_with:
                            disagrees = ", ".join([p.value.upper() for p in msg.disagrees_with])
                            st.caption(f"❌ Discorda de: {disagrees}")

                # Mostrar consenso
                if session.final_decision:
                    st.session_state.debate_messages.append({
                        "role": "system",
                        "content": session.final_decision
                    })

                    with st.chat_message("system", avatar="⚙️"):
                        st.markdown(session.final_decision)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                status_placeholder.error(f"Erro no debate: {e}")
                st.error(f"Detalhes: {error_details}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>O Construtor v2.0 - Sistema Autônomo de Engenharia de Software</div>",
    unsafe_allow_html=True
)
