"""
O Construtor - Interface Streamlit Avançada
Interface completa com orquestração de agentes, workflows e métricas
"""
import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Imports do sistema
from core.orchestrator import Orchestrator
from core.event_bus import EventBus
from core.memory_store import MemoryStore
from core.task_queue import TaskQueue
from config.models import TaskType

# Carrega variáveis de ambiente
load_dotenv()

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
    ["🏠 Dashboard", "🤖 Agentes", "📋 Tarefas", "🔄 Workflows", "📊 Métricas", "💬 Chat"]
)

st.sidebar.markdown("---")

# Status do sistema
if system_ready:
    st.sidebar.success("✅ Sistema Operacional")
    st.sidebar.metric("Agentes Ativos", len(orchestrator._agents) if orchestrator else 0)
    st.sidebar.metric("Tarefas Pendentes", task_queue.size() if task_queue else 0)
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
        st.metric("Agentes", len(orchestrator._agents))
    with col2:
        st.metric("Tarefas Concluídas", 0)  # TODO: pegar do orchestrator
    with col3:
        st.metric("Em Andamento", task_queue.size())
    with col4:
        st.metric("Taxa de Sucesso", "95%")

    st.markdown("---")

    # Lista de agentes
    st.subheader("🤖 Agentes Disponíveis")

    agents_info = [
        {"nome": "Arquiteto", "emoji": "🏛️", "modelo": "Claude Opus 4.5", "status": "Idle"},
        {"nome": "Desenvolvedor", "emoji": "👨‍💻", "modelo": "Claude Code + Gemini", "status": "Idle"},
        {"nome": "Revisor", "emoji": "🔍", "modelo": "Gemini 3 Pro", "status": "Idle"},
        {"nome": "Tester", "emoji": "🧪", "modelo": "Gemini 2.5 Flash", "status": "Idle"},
        {"nome": "DevOps (Jules)", "emoji": "🚀", "modelo": "Gemini 2.5 Pro", "status": "Idle"},
        {"nome": "Segurança", "emoji": "🔐", "modelo": "Gemini 3 Pro", "status": "Idle"},
        {"nome": "Otimizador", "emoji": "⚡", "modelo": "Gemini 3 Pro", "status": "Idle"},
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
    st.title("💬 Chat com O Construtor")

    # Inicializa histórico
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Botão limpar
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

    # Mostra histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta do assistente
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ Processando...")

            try:
                # TODO: Integrar com orquestrador para processar comando
                response = f"Recebi sua solicitação: '{prompt}'. Analisando e distribuindo para os agentes apropriados..."

                placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                placeholder.error(f"Erro: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>O Construtor v2.0 - Sistema Autônomo de Engenharia de Software</div>",
    unsafe_allow_html=True
)
