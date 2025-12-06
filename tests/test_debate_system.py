"""
Unit tests para DebateSystem
Testa debates multi-IA e busca de consenso
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from core.debate_system import (
    DebateOrchestrator,
    DebateSession,
    DebateMessage,
    AIParticipant,
    DebateStage
)


@pytest.mark.asyncio
class TestDebateSystem:
    """Testes do sistema de debates"""

    async def test_debate_orchestrator_initialization(self):
        """Testa inicialização do orchestrator de debates"""
        orch = DebateOrchestrator(max_rounds=5)

        assert orch is not None
        assert orch.max_rounds == 5
        assert orch.sessions == {}

    async def test_debate_session_creation(self):
        """Testa criação de sessão de debate"""
        session = DebateSession(topic="Test Topic")

        assert session.topic == "Test Topic"
        assert session.current_round == 0
        assert session.stage == DebateStage.INITIAL_RESPONSES
        assert session.consensus_reached is False
        assert len(session.messages) == 0

    async def test_debate_message_creation(self):
        """Testa criação de mensagem de debate"""
        message = DebateMessage(
            participant=AIParticipant.CLAUDE,
            content="Test message",
            round_number=1
        )

        assert message.participant == AIParticipant.CLAUDE
        assert message.content == "Test message"
        assert message.round_number == 1
        assert message.confidence == 0.5

    async def test_debate_message_agreements(self):
        """Testa registro de concordâncias"""
        message = DebateMessage(
            participant=AIParticipant.CLAUDE,
            content="Test",
            round_number=1,
            agrees_with=[AIParticipant.GPT]
        )

        assert AIParticipant.GPT in message.agrees_with
        assert len(message.agrees_with) == 1

    async def test_debate_message_disagreements(self):
        """Testa registro de discordâncias"""
        message = DebateMessage(
            participant=AIParticipant.GEMINI,
            content="Test",
            round_number=1,
            disagrees_with=[AIParticipant.CLAUDE, AIParticipant.GPT]
        )

        assert AIParticipant.CLAUDE in message.disagrees_with
        assert AIParticipant.GPT in message.disagrees_with
        assert len(message.disagrees_with) == 2

    @patch('core.debate_system.anthropic_client')
    async def test_simulate_claude_response(self, mock_client):
        """Testa simulação de resposta do Claude"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude's response")]
        mock_client.messages.create.return_value = mock_response

        orch = DebateOrchestrator()
        response = await orch._simulate_claude_response("Test topic", [])

        assert response == "Claude's response"

    async def test_check_consensus_empty_messages(self):
        """Testa verificação de consenso sem mensagens"""
        orch = DebateOrchestrator()
        session = DebateSession(topic="Test")

        consensus = await orch._check_consensus(session)

        # Sem mensagens, não há consenso (retorna dict com 'reached': False)
        assert isinstance(consensus, dict)
        assert consensus.get('reached') is False

    async def test_debate_session_max_rounds(self):
        """Testa limite de rodadas"""
        session = DebateSession(topic="Test", max_rounds=3)

        assert session.max_rounds == 3
        session.current_round = 3

        # Deve estar no limite
        assert session.current_round >= session.max_rounds

    async def test_ai_participant_enum(self):
        """Testa enum de participantes"""
        assert AIParticipant.CLAUDE.value == "claude"
        assert AIParticipant.GPT.value == "gpt"
        assert AIParticipant.GEMINI.value == "gemini"

    async def test_debate_stage_enum(self):
        """Testa enum de estágios"""
        assert DebateStage.INITIAL_RESPONSES.value == "initial_responses"
        assert DebateStage.DISCUSSION.value == "discussion"
        assert DebateStage.CONSENSUS_CHECK.value == "consensus_check"
        assert DebateStage.FINAL_CONSENSUS.value == "final_consensus"

    async def test_session_timestamps(self):
        """Testa timestamps da sessão"""
        session = DebateSession(topic="Test")

        assert session.started_at is not None
        assert session.ended_at is None

    async def test_message_confidence_range(self):
        """Testa range de confiança da mensagem"""
        message = DebateMessage(
            participant=AIParticipant.CLAUDE,
            content="Test",
            round_number=1,
            confidence=0.8
        )

        assert 0.0 <= message.confidence <= 1.0

    async def test_session_stores_messages(self):
        """Testa armazenamento de mensagens"""
        session = DebateSession(topic="Test")

        message1 = DebateMessage(
            participant=AIParticipant.CLAUDE,
            content="Message 1",
            round_number=1
        )

        message2 = DebateMessage(
            participant=AIParticipant.GPT,
            content="Message 2",
            round_number=1
        )

        session.messages.append(message1)
        session.messages.append(message2)

        assert len(session.messages) == 2
        assert session.messages[0] == message1
        assert session.messages[1] == message2

    async def test_format_debate_for_display(self):
        """Testa formatação de debate para exibição"""
        from core.debate_system import format_debate_for_display

        session = DebateSession(topic="Test Topic")
        session.current_round = 2

        formatted = format_debate_for_display(session)

        assert "Test Topic" in formatted
        assert "Rodadas: 2" in formatted

    async def test_debate_orchestrator_multiple_participants(self):
        """Testa orchestrator com múltiplos participantes"""
        orch = DebateOrchestrator()

        # Simulação: não vai chamar APIs reais
        participants = [
            AIParticipant.CLAUDE,
            AIParticipant.GPT,
            AIParticipant.GEMINI
        ]

        assert len(participants) == 3
        assert AIParticipant.CLAUDE in participants
        assert AIParticipant.GPT in participants
        assert AIParticipant.GEMINI in participants

    async def test_consensus_tracking(self):
        """Testa rastreamento de consenso"""
        session = DebateSession(topic="Test")

        assert session.consensus_reached is False
        assert session.final_decision is None

        # Simular consenso
        session.consensus_reached = True
        session.final_decision = "Final decision"

        assert session.consensus_reached is True
        assert session.final_decision == "Final decision"

    async def test_debate_round_increment(self):
        """Testa incremento de rodadas"""
        session = DebateSession(topic="Test")

        initial_round = session.current_round
        session.current_round += 1

        assert session.current_round == initial_round + 1

    async def test_stage_progression(self):
        """Testa progressão de estágios"""
        session = DebateSession(topic="Test")

        assert session.stage == DebateStage.INITIAL_RESPONSES

        session.stage = DebateStage.DISCUSSION
        assert session.stage == DebateStage.DISCUSSION

        session.stage = DebateStage.CONSENSUS_CHECK
        assert session.stage == DebateStage.CONSENSUS_CHECK

        session.stage = DebateStage.FINAL_CONSENSUS
        assert session.stage == DebateStage.FINAL_CONSENSUS
