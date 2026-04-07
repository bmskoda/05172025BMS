"""Tests for the AEGIS AI Agent Team module."""

from __future__ import annotations

import asyncio
import json
import pytest

from aegis.agents.agent_team import (
    AgentCredential,
    AgentDiscipline,
    AgentRole,
    AgentTeamOrchestrator,
    HuggingFaceBackend,
    ModelRegistry,
    OpenAICompatibleBackend,
    ResearchAgent,
    ResearchOutput,
    ResearchTask,
    VLLMBackend,
)


# ── helpers ──────────────────────────────────────────────────────────────


class StubBackend(VLLMBackend):
    """In-process stub that echoes the prompt without hitting any server."""

    def __init__(self, backend_id: str = "stub", model_name: str = "stub-model"):
        super().__init__(backend_id, model_name, base_url="http://stub:0/v1")

    async def generate(self, prompt, **kwargs):
        self._request_count += 1
        self._healthy = True
        return {
            "text": f"[STUB RESPONSE] {prompt[:120]}",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            "latency_ms": 1.0,
        }

    async def health_check(self):
        self._healthy = True
        return True

    async def close(self):
        pass


def _make_registry() -> ModelRegistry:
    reg = ModelRegistry()
    stub = StubBackend()
    reg.register(
        stub,
        capabilities=[
            "general_research",
            "legal_analysis",
            "code_analysis",
            "scientific_research",
            "medical_research",
            "financial_analysis",
            "multilingual",
        ],
    )
    return reg


# ── tests ────────────────────────────────────────────────────────────────


class TestModelRegistry:
    def test_register_and_lookup(self):
        reg = _make_registry()
        assert reg.get("stub") is not None
        assert reg.get("nonexistent") is None

    def test_capability_lookup(self):
        reg = _make_registry()
        backends = reg.get_by_capability("legal_analysis")
        assert len(backends) == 1
        assert backends[0].backend_id == "stub"

    @pytest.mark.asyncio
    async def test_best_backend(self):
        reg = _make_registry()
        best = await reg.get_best_backend("code_analysis")
        assert best is not None

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        reg = _make_registry()
        results = await reg.health_check_all()
        assert results["stub"] is True

    def test_summary(self):
        reg = _make_registry()
        s = reg.summary
        assert s["backend_count"] == 1
        assert "stub" in s["backends"]


class TestResearchAgent:
    @pytest.mark.asyncio
    async def test_execute_task(self):
        reg = _make_registry()
        agent = ResearchAgent(
            name="Test Agent",
            discipline=AgentDiscipline.COMPUTER_SCIENCE,
            credentials=[AgentCredential.PHD],
            model_registry=reg,
        )
        task = ResearchTask(
            query="What is P vs NP?",
            context="Complexity theory",
        )
        output = await agent.execute(task)
        assert output.output_text.startswith("[STUB RESPONSE]")
        assert output.hash != ""
        assert output.model_used == "stub-model"

    def test_system_prompt_includes_credentials(self):
        agent = ResearchAgent(
            discipline=AgentDiscipline.LAW,
            credentials=[AgentCredential.JD, AgentCredential.PHD],
        )
        assert "J.D." in agent.system_prompt
        assert "Ph.D." in agent.system_prompt
        assert "Law" in agent.system_prompt

    def test_profile(self):
        agent = ResearchAgent(
            name="Prof. X",
            discipline=AgentDiscipline.PHYSICS,
            role=AgentRole.LEAD_RESEARCHER,
        )
        p = agent.profile
        assert p["name"] == "Prof. X"
        assert p["discipline"] == "Physics"
        assert p["role"] == "lead_researcher"


class TestAgentTeamOrchestrator:
    @pytest.mark.asyncio
    async def test_spawn_agent(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        agent = orch.spawn_agent(AgentDiscipline.MATHEMATICS)
        assert agent.agent_id in orch._agents
        assert agent.discipline == AgentDiscipline.MATHEMATICS

    @pytest.mark.asyncio
    async def test_spawn_full_stanford_team(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        agents = orch.spawn_full_stanford_team()
        assert len(agents) == len(AgentDiscipline)
        disciplines = {a.discipline for a in agents}
        assert disciplines == set(AgentDiscipline)

    @pytest.mark.asyncio
    async def test_assign_task(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        task = ResearchTask(query="Explain quantum entanglement")
        output = await orch.assign_task(
            task, discipline=AgentDiscipline.PHYSICS
        )
        assert "[STUB RESPONSE]" in output.output_text
        assert len(orch._audit_log) == 1
        assert orch._audit_log[0]["event"] == "task_completed"

    @pytest.mark.asyncio
    async def test_fan_out(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        task = ResearchTask(query="Analyse this contract")
        outputs = await orch.fan_out(
            task,
            [
                AgentDiscipline.LAW,
                AgentDiscipline.FINANCE,
                AgentDiscipline.COMPUTER_SCIENCE,
            ],
        )
        assert len(outputs) == 3
        assert all(o.output_text for o in outputs)

    @pytest.mark.asyncio
    async def test_research_and_synthesise(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        result = await orch.research_and_synthesise(
            query="Impact of AI on patent law",
            disciplines=[
                AgentDiscipline.ARTIFICIAL_INTELLIGENCE,
                AgentDiscipline.INTELLECTUAL_PROPERTY_LAW,
            ],
        )
        assert "discipline_outputs" in result
        assert len(result["discipline_outputs"]) == 2
        assert "synthesis" in result
        assert result["synthesis"]["text"]

    @pytest.mark.asyncio
    async def test_team_summary(self):
        orch = AgentTeamOrchestrator(model_registry=_make_registry())
        orch.spawn_full_stanford_team()
        summary = orch.team_summary
        assert summary["total_agents"] == len(AgentDiscipline)
        assert summary["model_registry"]["backend_count"] == 1


class TestVLLMBackend:
    def test_instantiation(self):
        backend = VLLMBackend(
            "vllm-test",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            base_url="http://localhost:8000/v1",
        )
        assert backend.model_name == "meta-llama/Meta-Llama-3.1-70B-Instruct"
        assert backend.base_url == "http://localhost:8000/v1"

    def test_stats_initial(self):
        backend = VLLMBackend("v1", "model-a")
        s = backend.stats
        assert s["requests"] == 0
        assert s["errors"] == 0


class TestHuggingFaceBackend:
    def test_instantiation(self):
        backend = HuggingFaceBackend(
            "hf-test",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
        )
        assert backend.model_name == "mistralai/Mixtral-8x22B-Instruct-v0.1"


class TestOpenAICompatibleBackend:
    def test_instantiation(self):
        backend = OpenAICompatibleBackend(
            "oai-test",
            "gpt-4",
            base_url="https://api.openai.com/v1",
        )
        assert backend.model_name == "gpt-4"


class TestResearchOutput:
    def test_compute_hash(self):
        out = ResearchOutput(
            task_id="t1",
            agent_id="a1",
            output_text="hello",
        )
        h = out.compute_hash()
        assert len(h) == 64  # sha3-256 hex
        assert out.hash == h

    def test_hash_deterministic(self):
        out1 = ResearchOutput(
            task_id="t1",
            agent_id="a1",
            output_text="hello",
            timestamp="2026-01-01T00:00:00",
        )
        out2 = ResearchOutput(
            task_id="t1",
            agent_id="a1",
            output_text="hello",
            timestamp="2026-01-01T00:00:00",
        )
        assert out1.compute_hash() == out2.compute_hash()


class TestEnumerationCompleteness:
    def test_all_stanford_disciplines_present(self):
        assert len(AgentDiscipline) >= 60

    def test_credentials_include_all_requested(self):
        names = {c.value for c in AgentCredential}
        assert "Ph.D." in names
        assert "J.D." in names
        assert "M.B.A." in names
        assert "C.P.A." in names
        assert "C.F.A." in names
        assert "C.V.A." in names
        assert "M.S.E.E." in names
        assert "M.S.M.E." in names
        assert "M.L.S." in names
        assert "Postdoctoral Fellow" in names
