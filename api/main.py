"""
O Construtor - API Server
FastAPI application para orquestração de agentes
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import tasks, agents, health, workflows
from core.orchestrator import Orchestrator
from core.event_bus import EventBus
from core.memory_store import MemoryStore
from core.task_queue import TaskQueue

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instâncias globais
orchestrator: Orchestrator = None
event_bus: EventBus = None
memory_store: MemoryStore = None
task_queue: TaskQueue = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    global orchestrator, event_bus, memory_store, task_queue

    logger.info("Inicializando O Construtor...")

    # Inicializa componentes core
    event_bus = EventBus()
    memory_store = MemoryStore()
    task_queue = TaskQueue()
    orchestrator = Orchestrator(
        event_bus=event_bus,
        memory_store=memory_store,
        task_queue=task_queue
    )

    await orchestrator.initialize()

    logger.info("O Construtor inicializado com sucesso!")

    yield

    # Cleanup
    logger.info("Encerrando O Construtor...")
    await orchestrator.shutdown()


# Cria aplicação FastAPI
app = FastAPI(
    title="O Construtor API",
    description="Sistema Autônomo de Engenharia de Software",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "name": "O Construtor API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para streaming de eventos"""
    await websocket.accept()

    client_id = id(websocket)
    logger.info(f"Cliente WebSocket conectado: {client_id}")

    # Subscreve aos eventos
    async def event_handler(event):
        try:
            await websocket.send_json(event)
        except:
            pass

    event_bus.subscribe("*", event_handler)

    try:
        while True:
            # Mantém conexão aberta
            data = await websocket.receive_text()
            logger.debug(f"Recebido do cliente {client_id}: {data}")
    except WebSocketDisconnect:
        logger.info(f"Cliente WebSocket desconectado: {client_id}")
        event_bus.unsubscribe("*", event_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Torna componentes acessíveis globalmente
def get_orchestrator() -> Orchestrator:
    return orchestrator

def get_event_bus() -> EventBus:
    return event_bus

def get_memory_store() -> MemoryStore:
    return memory_store

def get_task_queue() -> TaskQueue:
    return task_queue
