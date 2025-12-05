"""
Sistema de Debate Multi-IA com Consenso
========================================

As IAs debatem entre si até chegarem a um consenso.
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

# Importar clientes das APIs
import anthropic
from openai import OpenAI
import google.generativeai as genai

# Configurar APIs
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Inicializar clientes
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


class DebateStage(Enum):
    """Estágios do debate"""
    INITIAL_RESPONSES = "initial_responses"
    DISCUSSION = "discussion"
    CONSENSUS_CHECK = "consensus_check"
    FINAL_CONSENSUS = "final_consensus"


class AIParticipant(Enum):
    """Participantes do debate"""
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"


@dataclass
class DebateMessage:
    """Mensagem de um participante no debate"""
    participant: AIParticipant
    content: str
    round_number: int
    timestamp: datetime = field(default_factory=datetime.now)
    agrees_with: List[AIParticipant] = field(default_factory=list)
    disagrees_with: List[AIParticipant] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 a 1.0


@dataclass
class DebateSession:
    """Sessão de debate entre IAs"""
    topic: str
    messages: List[DebateMessage] = field(default_factory=list)
    current_round: int = 0
    max_rounds: int = 5
    stage: DebateStage = DebateStage.INITIAL_RESPONSES
    consensus_reached: bool = False
    final_decision: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None


class DebateOrchestrator:
    """Orquestra debates entre múltiplas IAs"""

    def __init__(self, max_rounds: int = 5):
        self.max_rounds = max_rounds
        self.sessions: Dict[str, DebateSession] = {}

    async def start_debate(
        self,
        topic: str,
        participants: List[AIParticipant] = None
    ) -> DebateSession:
        """
        Inicia um novo debate entre as IAs.

        Args:
            topic: Tópico para debate
            participants: Lista de participantes (padrão: todos)

        Returns:
            Sessão de debate
        """
        if participants is None:
            participants = [AIParticipant.CLAUDE, AIParticipant.GPT, AIParticipant.GEMINI]

        session = DebateSession(
            topic=topic,
            max_rounds=self.max_rounds
        )

        # Rodada 1: Respostas iniciais
        print(f"\n{'='*70}")
        print(f"NOVO DEBATE: {topic}")
        print(f"{'='*70}\n")

        session.stage = DebateStage.INITIAL_RESPONSES
        print(f"[Rodada 1] Respostas Iniciais")
        print("-" * 70)

        initial_responses = await self._get_initial_responses(topic, participants)
        for participant, response in initial_responses.items():
            message = DebateMessage(
                participant=participant,
                content=response,
                round_number=1,
                confidence=0.7
            )
            session.messages.append(message)
            print(f"\n[{participant.value.upper()}]:\n{response}")

        session.current_round = 1

        # Rodadas 2+: Discussão
        session.stage = DebateStage.DISCUSSION
        while session.current_round < session.max_rounds and not session.consensus_reached:
            session.current_round += 1
            print(f"\n{'='*70}")
            print(f"[Rodada {session.current_round}] Discussão")
            print("-" * 70)

            # Cada IA lê as respostas anteriores e comenta
            for participant in participants:
                previous_messages = [m for m in session.messages if m.participant != participant]
                response = await self._get_discussion_response(
                    participant=participant,
                    topic=topic,
                    previous_messages=previous_messages,
                    round_number=session.current_round
                )

                message = DebateMessage(
                    participant=participant,
                    content=response["content"],
                    round_number=session.current_round,
                    agrees_with=response.get("agrees_with", []),
                    disagrees_with=response.get("disagrees_with", []),
                    confidence=response.get("confidence", 0.5)
                )
                session.messages.append(message)
                print(f"\n[{participant.value.upper()}]:\n{response['content']}")

            # Verificar consenso
            session.stage = DebateStage.CONSENSUS_CHECK
            consensus_check = await self._check_consensus(session)

            if consensus_check["reached"]:
                session.consensus_reached = True
                session.final_decision = consensus_check["decision"]
                session.stage = DebateStage.FINAL_CONSENSUS
                print(f"\n{'='*70}")
                print("CONSENSO ALCANCADO!")
                print(f"{'='*70}")
                print(f"\n{consensus_check['decision']}")
                break

        session.ended_at = datetime.now()
        return session

    async def _get_initial_responses(
        self,
        topic: str,
        participants: List[AIParticipant]
    ) -> Dict[AIParticipant, str]:
        """Obtém respostas iniciais de cada participante"""
        responses = {}

        # Simular respostas (na prática, chamaria as APIs reais)
        if AIParticipant.CLAUDE in participants:
            responses[AIParticipant.CLAUDE] = await self._simulate_claude_response(topic, [])

        if AIParticipant.GPT in participants:
            responses[AIParticipant.GPT] = await self._simulate_gpt_response(topic, [])

        if AIParticipant.GEMINI in participants:
            responses[AIParticipant.GEMINI] = await self._simulate_gemini_response(topic, [])

        return responses

    async def _get_discussion_response(
        self,
        participant: AIParticipant,
        topic: str,
        previous_messages: List[DebateMessage],
        round_number: int
    ) -> Dict:
        """Obtém resposta de discussão considerando mensagens anteriores"""

        # Formatar contexto com mensagens anteriores
        context = f"Topico: {topic}\n\nRespostas anteriores:\n"
        for msg in previous_messages:
            if msg.round_number == round_number - 1 or msg.round_number == round_number:
                context += f"\n[{msg.participant.value.upper()}]: {msg.content}\n"

        # Simular resposta (na prática, chamaria as APIs)
        if participant == AIParticipant.CLAUDE:
            content = await self._simulate_claude_response(topic, previous_messages)
        elif participant == AIParticipant.GPT:
            content = await self._simulate_gpt_response(topic, previous_messages)
        else:  # GEMINI
            content = await self._simulate_gemini_response(topic, previous_messages)

        # Analisar concordância/discordância
        agrees_with = []
        disagrees_with = []

        # Lógica simples para detectar acordo/desacordo
        if "concordo" in content.lower() or "agree" in content.lower():
            # Detectar com quem concorda
            for msg in previous_messages:
                if msg.participant.value in content.lower():
                    agrees_with.append(msg.participant)

        if "discordo" in content.lower() or "disagree" in content.lower():
            for msg in previous_messages:
                if msg.participant.value in content.lower():
                    disagrees_with.append(msg.participant)

        # Calcular confiança baseado na rodada
        confidence = max(0.5, 1.0 - (round_number * 0.1))

        return {
            "content": content,
            "agrees_with": agrees_with,
            "disagrees_with": disagrees_with,
            "confidence": confidence
        }

    async def _check_consensus(self, session: DebateSession) -> Dict:
        """Verifica se houve consenso entre os participantes"""

        # Pegar mensagens da última rodada
        last_round_messages = [
            m for m in session.messages
            if m.round_number == session.current_round
        ]

        # Verificar se todos concordam
        agreements = sum(len(m.agrees_with) for m in last_round_messages)
        disagreements = sum(len(m.disagrees_with) for m in last_round_messages)

        # Critério simples: mais acordos que desacordos
        if agreements > disagreements and session.current_round >= 2:
            # Sintetizar decisão final
            decision = await self._synthesize_consensus(session)
            return {
                "reached": True,
                "decision": decision,
                "confidence": agreements / (agreements + disagreements + 1)
            }

        # Após rodada final, forçar síntese mesmo sem consenso perfeito
        if session.current_round >= session.max_rounds:
            decision = await self._synthesize_consensus(session)
            return {
                "reached": True,
                "decision": decision,
                "confidence": 0.6
            }

        return {"reached": False}

    async def _synthesize_consensus(self, session: DebateSession) -> str:
        """Sintetiza a decisão final baseado em todas as mensagens"""

        synthesis = f"\n=== DECISAO FINAL CONSOLIDADA ===\n\n"
        synthesis += f"Topico: {session.topic}\n\n"
        synthesis += f"Apos {session.current_round} rodadas de debate, "
        synthesis += f"os participantes chegaram ao seguinte consenso:\n\n"

        # Pegar pontos principais de cada IA na última rodada
        last_messages = [
            m for m in session.messages
            if m.round_number == session.current_round
        ]

        synthesis += "PRINCIPAIS PONTOS:\n\n"
        for msg in last_messages:
            synthesis += f"- {msg.participant.value.upper()}: "
            # Pegar primeira sentença
            first_sentence = msg.content.split('.')[0] + '.'
            synthesis += f"{first_sentence}\n"

        synthesis += f"\nCONCLUSAO:\n"
        synthesis += f"Baseado no debate, a solucao recomendada e..."

        # TODO: Em produção, usar uma IA para sintetizar de verdade
        return synthesis

    # ============================================================
    # CHAMADAS REAIS ÀS APIs
    # ============================================================

    async def _simulate_claude_response(
        self,
        topic: str,
        previous_messages: List[DebateMessage]
    ) -> str:
        """Chama API REAL do Claude (Anthropic)"""
        if not anthropic_client:
            return "[Claude Opus] API key nao configurada. Configure ANTHROPIC_API_KEY no .env"

        try:
            # Construir prompt com contexto
            if not previous_messages:
                prompt = (
                    f"Voce e Claude Opus, especialista em arquitetura de sistemas.\n\n"
                    f"Topico para analise: {topic}\n\n"
                    f"De sua perspectiva arquitetural profunda, analise este topico. "
                    f"Seja conciso mas tecnico. Foque em design, escalabilidade e trade-offs."
                )
            else:
                # Incluir mensagens anteriores para contexto
                context = "\n\n".join([
                    f"{m.participant.value.upper()}: {m.content}"
                    for m in previous_messages[-3:]  # Últimas 3 mensagens
                ])
                prompt = (
                    f"Voce e Claude Opus, especialista em arquitetura.\n\n"
                    f"Topico: {topic}\n\n"
                    f"Respostas anteriores dos outros participantes:\n{context}\n\n"
                    f"Agora responda considerando o que foi dito. Concorde, discorde ou "
                    f"adicione perspectivas arquiteturais importantes. Seja direto e tecnico."
                )

            # Chamar API real
            response = anthropic_client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            return f"[Claude Opus] Erro ao chamar API: {str(e)}"

    async def _simulate_gpt_response(
        self,
        topic: str,
        previous_messages: List[DebateMessage]
    ) -> str:
        """Chama API REAL do GPT (OpenAI)"""
        if not openai_client:
            return "[GPT-5.1] API key nao configurada. Configure OPENAI_API_KEY no .env"

        try:
            # Construir prompt
            if not previous_messages:
                prompt = (
                    f"Voce e GPT-5.1, especialista em implementacao pratica de software.\n\n"
                    f"Topico: {topic}\n\n"
                    f"De sua perspectiva pragmatica de desenvolvedor senior, analise este topico. "
                    f"Foque em implementacao, praticidade e time-to-market. Seja conciso."
                )
            else:
                context = "\n\n".join([
                    f"{m.participant.value.upper()}: {m.content}"
                    for m in previous_messages[-3:]
                ])
                prompt = (
                    f"Voce e GPT-5.1, especialista em implementacao.\n\n"
                    f"Topico: {topic}\n\n"
                    f"Respostas anteriores:\n{context}\n\n"
                    f"Responda considerando o contexto. Adicione perspectiva de implementacao pratica. "
                    f"Concorde, discorde ou complemente. Seja direto."
                )

            # Chamar API real
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Usar gpt-4o por enquanto (gpt-5.1 ainda não disponível)
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "Voce e um desenvolvedor senior pragmatico."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"[GPT-4o] Erro ao chamar API: {str(e)}"

    async def _simulate_gemini_response(
        self,
        topic: str,
        previous_messages: List[DebateMessage]
    ) -> str:
        """Chama API REAL do Gemini (Google)"""
        if not GOOGLE_API_KEY:
            return "[Gemini 2.5 Pro] API key nao configurada. Configure GOOGLE_API_KEY no .env"

        try:
            # Construir prompt
            if not previous_messages:
                prompt = (
                    f"Voce e Gemini 2.5 Pro, especialista em performance e seguranca.\n\n"
                    f"Topico: {topic}\n\n"
                    f"Analise sob a otica de performance, otimizacao e seguranca. "
                    f"Seja tecnico e focado em eficiencia. Conciso."
                )
            else:
                context = "\n\n".join([
                    f"{m.participant.value.upper()}: {m.content}"
                    for m in previous_messages[-3:]
                ])
                prompt = (
                    f"Voce e Gemini 2.5 Pro, especialista em performance e seguranca.\n\n"
                    f"Topico: {topic}\n\n"
                    f"Respostas anteriores:\n{context}\n\n"
                    f"Responda considerando performance e seguranca. "
                    f"Concorde, discorde ou adicione analise tecnica. Direto ao ponto."
                )

            # Chamar API real
            model = genai.GenerativeModel('gemini-2.5-pro')  # Modelo estável
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )

            return response.text

        except Exception as e:
            return f"[Gemini Pro] Erro ao chamar API: {str(e)}"


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def format_debate_for_display(session: DebateSession) -> str:
    """Formata debate para exibição"""
    output = []

    output.append("=" * 70)
    output.append(f"DEBATE: {session.topic}")
    output.append("=" * 70)
    output.append(f"Rodadas: {session.current_round}/{session.max_rounds}")
    output.append(f"Status: {'Consenso alcancado' if session.consensus_reached else 'Em andamento'}")
    output.append("=" * 70)
    output.append("")

    current_round = 0
    for msg in session.messages:
        if msg.round_number != current_round:
            current_round = msg.round_number
            output.append("")
            output.append(f"[RODADA {current_round}]")
            output.append("-" * 70)

        output.append(f"\n[{msg.participant.value.upper()}]:")
        output.append(msg.content)

        if msg.agrees_with:
            agrees = ", ".join([p.value.upper() for p in msg.agrees_with])
            output.append(f"  -> Concorda com: {agrees}")

        if msg.disagrees_with:
            disagrees = ", ".join([p.value.upper() for p in msg.disagrees_with])
            output.append(f"  -> Discorda de: {disagrees}")

    if session.final_decision:
        output.append("")
        output.append("=" * 70)
        output.append("DECISAO FINAL")
        output.append("=" * 70)
        output.append(session.final_decision)

    return "\n".join(output)
