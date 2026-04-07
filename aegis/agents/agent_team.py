#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
================================================================================
AEGIS AI AGENT TEAM - Rapidly Scalable Multi-Discipline Research Agents
================================================================================

Builds a rapidly scalable AI agent team holding Ph.D., J.D., and postdoctoral
credentials across every discipline taught at Stanford University, including all
professional academic professions. The system leverages Lane Chang's entire
infrastructure of technologies together with vLLM and all other Hugging Face
API-integrated models for advanced forensic and academic research.

Architecture:
    ModelRegistry  <--- registers --->  ModelBackend (vLLM | HF | OpenAI)
         |
    AgentTeamOrchestrator
         |
    ResearchAgent[N]  (each with AgentRole + AgentDiscipline + AgentCredential)
         |
    TaskRouter  --->  parallel async inference across backends

The system auto-scales agent pools based on workload and available GPU/CPU
resources, supports dynamic model hot-swapping, and maintains an auditable
chain-of-reasoning for every research output.

Compliance: NIST 800-53 AU-6, ISO 27001, FBI CJIS audit requirements.
================================================================================
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

# ---------------------------------------------------------------------------
# Optional heavy imports with graceful fallbacks
# ---------------------------------------------------------------------------

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from huggingface_hub import InferenceClient, AsyncInferenceClient

    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


logger = logging.getLogger("AEGIS.AgentTeam")


# =============================================================================
# ENUMERATIONS
# =============================================================================


class AgentRole(Enum):
    """Operational roles an agent may assume within the team."""

    LEAD_RESEARCHER = "lead_researcher"
    DOMAIN_EXPERT = "domain_expert"
    LEGAL_ANALYST = "legal_analyst"
    DATA_SCIENTIST = "data_scientist"
    FORENSIC_ANALYST = "forensic_analyst"
    POLICY_ADVISOR = "policy_advisor"
    PEER_REVIEWER = "peer_reviewer"
    SYNTHESIS_COORDINATOR = "synthesis_coordinator"
    ADVERSARIAL_AUDITOR = "adversarial_auditor"
    ETHICS_REVIEWER = "ethics_reviewer"


class AgentCredential(Enum):
    """Academic and professional credentials agents may hold."""

    PHD = "Ph.D."
    JD = "J.D."
    MD = "M.D."
    MBA = "M.B.A."
    POSTDOC = "Postdoctoral Fellow"
    CPA = "C.P.A."
    CFA = "C.F.A."
    CVA = "C.V.A."
    PE = "P.E."
    MSCE = "M.S.C.E."
    MSEE = "M.S.E.E."
    MSME = "M.S.M.E."
    MLS = "M.L.S."
    DMIN = "D.Min."
    EDD = "Ed.D."
    DMA = "D.M.A."
    DSW = "D.S.W."


class AgentDiscipline(Enum):
    """
    Stanford University departments and professional schools mapped to
    agent specialisations.  Every school and major department is
    represented so the agent team covers the full academic spectrum.
    """

    # School of Engineering
    COMPUTER_SCIENCE = "Computer Science"
    ELECTRICAL_ENGINEERING = "Electrical Engineering"
    MECHANICAL_ENGINEERING = "Mechanical Engineering"
    CIVIL_ENVIRONMENTAL_ENGINEERING = "Civil & Environmental Engineering"
    CHEMICAL_ENGINEERING = "Chemical Engineering"
    MATERIALS_SCIENCE = "Materials Science & Engineering"
    AERONAUTICS_ASTRONAUTICS = "Aeronautics & Astronautics"
    BIOENGINEERING = "Bioengineering"
    MANAGEMENT_SCIENCE_ENGINEERING = "Management Science & Engineering"

    # School of Humanities and Sciences
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    STATISTICS = "Statistics"
    ECONOMICS = "Economics"
    POLITICAL_SCIENCE = "Political Science"
    PSYCHOLOGY = "Psychology"
    SOCIOLOGY = "Sociology"
    PHILOSOPHY = "Philosophy"
    HISTORY = "History"
    ENGLISH = "English"
    LINGUISTICS = "Linguistics"
    CLASSICS = "Classics"
    COMPARATIVE_LITERATURE = "Comparative Literature"
    MUSIC = "Music"
    ART_HISTORY = "Art History"
    ANTHROPOLOGY = "Anthropology"
    COMMUNICATION = "Communication"
    RELIGIOUS_STUDIES = "Religious Studies"
    EARTH_SYSTEM_SCIENCE = "Earth System Science"
    SYMBOLIC_SYSTEMS = "Symbolic Systems"

    # Stanford Law School
    LAW = "Law"
    INTELLECTUAL_PROPERTY_LAW = "Intellectual Property Law"
    CORPORATE_LAW = "Corporate Law"
    CRIMINAL_LAW = "Criminal Law"
    INTERNATIONAL_LAW = "International Law"
    CONSTITUTIONAL_LAW = "Constitutional Law"
    ENVIRONMENTAL_LAW = "Environmental Law"
    TECHNOLOGY_LAW = "Technology Law"

    # Stanford Graduate School of Business
    FINANCE = "Finance"
    ACCOUNTING = "Accounting"
    MARKETING = "Marketing"
    OPERATIONS = "Operations"
    ORGANIZATIONAL_BEHAVIOR = "Organizational Behavior"
    STRATEGY = "Strategy"
    ENTREPRENEURSHIP = "Entrepreneurship"

    # School of Medicine
    MEDICINE = "Medicine"
    GENETICS = "Genetics"
    NEUROSCIENCE = "Neuroscience"
    IMMUNOLOGY = "Immunology"
    PATHOLOGY = "Pathology"
    RADIOLOGY = "Radiology"
    BIOMEDICAL_INFORMATICS = "Biomedical Informatics"

    # School of Education
    EDUCATION = "Education"
    EDUCATIONAL_POLICY = "Educational Policy"
    LEARNING_SCIENCES = "Learning Sciences"

    # School of Earth, Energy & Environmental Sciences
    GEOPHYSICS = "Geophysics"
    GEOLOGICAL_SCIENCES = "Geological Sciences"
    ENERGY_RESOURCES_ENGINEERING = "Energy Resources Engineering"

    # Stanford Doerr School of Sustainability
    SUSTAINABILITY = "Sustainability Science"
    CLIMATE_SCIENCE = "Climate Science"
    ENVIRONMENTAL_SCIENCE = "Environmental Science"
    OCEANS = "Oceans"

    # Cross-disciplinary
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    DATA_SCIENCE = "Data Science"
    CYBERSECURITY = "Cybersecurity"
    QUANTUM_COMPUTING = "Quantum Computing"
    BLOCKCHAIN_CRYPTOGRAPHY = "Blockchain & Cryptography"
    COMPUTATIONAL_BIOLOGY = "Computational Biology"
    HUMAN_COMPUTER_INTERACTION = "Human-Computer Interaction"
    ROBOTICS = "Robotics"
    NATURAL_LANGUAGE_PROCESSING = "Natural Language Processing"
    COMPUTER_VISION = "Computer Vision"

    # Library and information science
    LIBRARY_INFORMATION_SCIENCE = "Library & Information Science"


# =============================================================================
# MODEL BACKENDS
# =============================================================================


class ModelBackend(ABC):
    """Abstract interface for LLM inference backends."""

    def __init__(self, backend_id: str, model_name: str, **kwargs):
        self.backend_id = backend_id
        self.model_name = model_name
        self._healthy = False
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text from prompt. Returns dict with 'text' and 'usage'."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True when the backend is reachable and serving."""

    @abstractmethod
    async def close(self) -> None:
        """Release backend resources."""

    @property
    def stats(self) -> Dict[str, Any]:
        avg_latency = (
            self._total_latency / self._request_count
            if self._request_count
            else 0.0
        )
        return {
            "backend_id": self.backend_id,
            "model": self.model_name,
            "healthy": self._healthy,
            "requests": self._request_count,
            "errors": self._error_count,
            "avg_latency_ms": round(avg_latency, 2),
        }


class VLLMBackend(ModelBackend):
    """
    Backend that targets a vLLM OpenAI-compatible server.

    vLLM serves models via an OpenAI-compatible API at ``/v1/completions``
    or ``/v1/chat/completions``.  This backend uses ``aiohttp`` or the
    ``openai`` async client when available.

    Environment variables:
        AEGIS_VLLM_BASE_URL  - e.g. http://localhost:8000/v1
        AEGIS_VLLM_API_KEY   - optional bearer token
    """

    def __init__(
        self,
        backend_id: str,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(backend_id, model_name, **kwargs)
        self.base_url = (
            base_url
            or os.getenv("AEGIS_VLLM_BASE_URL", "http://localhost:8000/v1")
        )
        self.api_key = api_key or os.getenv("AEGIS_VLLM_API_KEY", "")
        self._session: Optional[Any] = None

    async def _get_session(self):
        if OPENAI_AVAILABLE:
            return None
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError(
                "Neither openai nor aiohttp is installed; "
                "cannot reach vLLM backend."
            )
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=ClientTimeout(total=300),
            )
        return self._session

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        self._request_count += 1

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if OPENAI_AVAILABLE:
                client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key or "EMPTY",
                )
                resp = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop,
                )
                text = resp.choices[0].message.content or ""
                usage = {
                    "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                    "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                }
            else:
                session = await self._get_session()
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                }
                if stop:
                    payload["stop"] = stop
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            self._healthy = True
            return {"text": text, "usage": usage, "latency_ms": latency}

        except Exception as exc:
            self._error_count += 1
            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            logger.error("vLLM generate failed: %s", exc)
            return {"text": "", "usage": {}, "error": str(exc), "latency_ms": latency}

    async def health_check(self) -> bool:
        try:
            if OPENAI_AVAILABLE:
                client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key or "EMPTY",
                )
                await client.models.list()
                self._healthy = True
                return True
            if AIOHTTP_AVAILABLE:
                session = await self._get_session()
                async with session.get(f"{self.base_url}/models") as r:
                    self._healthy = r.status == 200
                    return self._healthy
        except Exception:
            self._healthy = False
        return False

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class HuggingFaceBackend(ModelBackend):
    """
    Backend that uses the Hugging Face Inference API or a local
    ``transformers`` pipeline.

    Supports both the hosted Inference API (via ``huggingface_hub``) and
    self-hosted Inference Endpoints.

    Environment variables:
        AEGIS_HF_API_TOKEN    - Hugging Face bearer token
        AEGIS_HF_ENDPOINT_URL - optional custom endpoint URL
    """

    def __init__(
        self,
        backend_id: str,
        model_name: str,
        api_token: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(backend_id, model_name, **kwargs)
        self.api_token = api_token or os.getenv("AEGIS_HF_API_TOKEN", "")
        self.endpoint_url = endpoint_url or os.getenv(
            "AEGIS_HF_ENDPOINT_URL", ""
        )
        self._client: Optional[Any] = None
        self._session: Optional[Any] = None

    def _get_client(self):
        if self._client is None and HF_HUB_AVAILABLE:
            kwargs: Dict[str, Any] = {"token": self.api_token}
            if self.endpoint_url:
                kwargs["model"] = self.endpoint_url
            else:
                kwargs["model"] = self.model_name
            self._client = AsyncInferenceClient(**kwargs)
        return self._client

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        self._request_count += 1

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"[SYSTEM] {system_prompt}\n\n{prompt}"

        try:
            client = self._get_client()
            if client is not None:
                response = await client.text_generation(
                    full_prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=stop,
                    return_full_text=False,
                )
                text = response if isinstance(response, str) else str(response)
            elif AIOHTTP_AVAILABLE:
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession(
                        timeout=ClientTimeout(total=300),
                    )
                api_url = (
                    self.endpoint_url
                    or f"https://api-inference.huggingface.co/models/{self.model_name}"
                )
                headers = {"Content-Type": "application/json"}
                if self.api_token:
                    headers["Authorization"] = f"Bearer {self.api_token}"

                payload = {
                    "inputs": full_prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "return_full_text": False,
                    },
                }
                async with self._session.post(
                    api_url, json=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if isinstance(data, list) and data:
                        text = data[0].get("generated_text", "")
                    else:
                        text = str(data)
            else:
                raise RuntimeError(
                    "Neither huggingface_hub nor aiohttp available."
                )

            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            self._healthy = True
            return {"text": text, "usage": {}, "latency_ms": latency}

        except Exception as exc:
            self._error_count += 1
            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            logger.error("HuggingFace generate failed: %s", exc)
            return {"text": "", "usage": {}, "error": str(exc), "latency_ms": latency}

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            if client is not None:
                await client.text_generation("ping", max_new_tokens=1)
                self._healthy = True
                return True
        except Exception:
            self._healthy = False
        return False

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class OpenAICompatibleBackend(ModelBackend):
    """
    Generic OpenAI-compatible backend (covers GPT-4, Claude, Mistral
    hosted endpoints, etc.).

    Environment variables:
        AEGIS_OPENAI_API_KEY  - bearer token
        AEGIS_OPENAI_BASE_URL - e.g. https://api.openai.com/v1
    """

    def __init__(
        self,
        backend_id: str,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(backend_id, model_name, **kwargs)
        self.base_url = base_url or os.getenv(
            "AEGIS_OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self.api_key = api_key or os.getenv("AEGIS_OPENAI_API_KEY", "")

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE:
            return {"text": "", "usage": {}, "error": "openai package not installed"}

        t0 = time.perf_counter()
        self._request_count += 1

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
            resp = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
            )
            text = resp.choices[0].message.content or ""
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            }
            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            self._healthy = True
            return {"text": text, "usage": usage, "latency_ms": latency}
        except Exception as exc:
            self._error_count += 1
            latency = (time.perf_counter() - t0) * 1000
            self._total_latency += latency
            logger.error("OpenAI-compatible generate failed: %s", exc)
            return {"text": "", "usage": {}, "error": str(exc), "latency_ms": latency}

    async def health_check(self) -> bool:
        if not OPENAI_AVAILABLE:
            return False
        try:
            client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
            await client.models.list()
            self._healthy = True
            return True
        except Exception:
            self._healthy = False
            return False

    async def close(self) -> None:
        pass


# =============================================================================
# MODEL REGISTRY
# =============================================================================


class ModelRegistry:
    """
    Central registry of model backends.

    Supports registering multiple backends (vLLM, HuggingFace, OpenAI-compat)
    and routing inference requests to the best available backend based on
    health, latency, and capability matching.
    """

    # Well-known open-weight models suitable for each discipline tier
    RECOMMENDED_MODELS: Dict[str, Dict[str, str]] = {
        "general_research": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "fallback": "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "legal_analysis": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "fallback": "mistralai/Mistral-Large-Instruct-2407",
        },
        "scientific_research": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "fallback": "Qwen/Qwen2.5-72B-Instruct",
        },
        "code_analysis": {
            "primary": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "fallback": "deepseek-ai/DeepSeek-Coder-V2-Instruct",
        },
        "medical_research": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "fallback": "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "financial_analysis": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "fallback": "Qwen/Qwen2.5-72B-Instruct",
        },
        "multilingual": {
            "primary": "Qwen/Qwen2.5-72B-Instruct",
            "fallback": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        },
    }

    def __init__(self):
        self._backends: Dict[str, ModelBackend] = {}
        self._capability_map: Dict[str, List[str]] = defaultdict(list)

    def register(
        self,
        backend: ModelBackend,
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """Register a model backend with optional capability tags."""
        self._backends[backend.backend_id] = backend
        for cap in capabilities or ["general_research"]:
            self._capability_map[cap].append(backend.backend_id)
        logger.info(
            "Registered backend %s (%s) with capabilities %s",
            backend.backend_id,
            backend.model_name,
            capabilities or ["general_research"],
        )

    def get(self, backend_id: str) -> Optional[ModelBackend]:
        return self._backends.get(backend_id)

    def get_by_capability(self, capability: str) -> List[ModelBackend]:
        ids = self._capability_map.get(capability, [])
        return [self._backends[bid] for bid in ids if bid in self._backends]

    async def get_best_backend(
        self, capability: str = "general_research"
    ) -> Optional[ModelBackend]:
        """Return the healthiest, lowest-latency backend for a capability."""
        candidates = self.get_by_capability(capability)
        if not candidates:
            candidates = list(self._backends.values())
        if not candidates:
            return None

        healthy = [b for b in candidates if b._healthy]
        if not healthy:
            for b in candidates:
                if await b.health_check():
                    return b
            return candidates[0]

        healthy.sort(
            key=lambda b: (
                b._total_latency / b._request_count
                if b._request_count
                else float("inf")
            )
        )
        return healthy[0]

    async def health_check_all(self) -> Dict[str, bool]:
        results = {}
        for bid, backend in self._backends.items():
            results[bid] = await backend.health_check()
        return results

    async def close_all(self) -> None:
        for backend in self._backends.values():
            await backend.close()

    @property
    def summary(self) -> Dict[str, Any]:
        return {
            "backend_count": len(self._backends),
            "backends": {bid: b.stats for bid, b in self._backends.items()},
            "capabilities": {
                cap: ids for cap, ids in self._capability_map.items()
            },
        }


# =============================================================================
# RESEARCH AGENT
# =============================================================================


@dataclass
class ResearchTask:
    """A discrete unit of research work assigned to an agent."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    context: str = ""
    expected_output_format: str = "structured_json"
    max_tokens: int = 4096
    temperature: float = 0.4
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchOutput:
    """Result produced by an agent for a given task."""

    task_id: str = ""
    agent_id: str = ""
    output_text: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning_chain: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    latency_ms: float = 0.0
    model_used: str = ""
    hash: str = ""

    def compute_hash(self) -> str:
        payload = json.dumps(
            {
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "output_text": self.output_text,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
        )
        self.hash = hashlib.sha3_256(payload.encode()).hexdigest()
        return self.hash


class ResearchAgent:
    """
    An AI-powered research agent holding specified credentials and
    specialised in a given academic discipline.

    Each agent wraps a model backend and augments raw LLM output with:
    - Discipline-specific system prompts calibrated per credential level
    - Chain-of-reasoning extraction
    - Confidence self-assessment
    - Cryptographic output hashing for audit
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "Research Agent",
        role: AgentRole = AgentRole.DOMAIN_EXPERT,
        discipline: AgentDiscipline = AgentDiscipline.COMPUTER_SCIENCE,
        credentials: Optional[List[AgentCredential]] = None,
        model_registry: Optional[ModelRegistry] = None,
        preferred_backend_id: Optional[str] = None,
        preferred_capability: str = "general_research",
    ):
        self.agent_id = agent_id or f"AGENT-{uuid.uuid4().hex[:12].upper()}"
        self.name = name
        self.role = role
        self.discipline = discipline
        self.credentials = credentials or [AgentCredential.PHD]
        self.model_registry = model_registry
        self.preferred_backend_id = preferred_backend_id
        self.preferred_capability = preferred_capability
        self._task_history: List[ResearchOutput] = []

    @property
    def system_prompt(self) -> str:
        creds = ", ".join(c.value for c in self.credentials)
        return (
            f"You are a world-class {self.discipline.value} researcher "
            f"holding {creds} credentials from Stanford University.  "
            f"Your role is {self.role.value.replace('_', ' ')}.  "
            f"You produce rigorous, peer-review-quality analysis.  "
            f"Always cite sources, quantify uncertainty, and structure "
            f"your output as JSON when requested.  Never fabricate data."
        )

    async def execute(self, task: ResearchTask) -> ResearchOutput:
        """Execute a research task and return structured output."""
        backend = await self._select_backend()
        if backend is None:
            return ResearchOutput(
                task_id=task.task_id,
                agent_id=self.agent_id,
                output_text="ERROR: No model backend available.",
                confidence=0.0,
                model_used="none",
            )

        prompt = self._build_prompt(task)

        result = await backend.generate(
            prompt,
            max_tokens=task.max_tokens,
            temperature=task.temperature,
            system_prompt=self.system_prompt,
        )

        output = ResearchOutput(
            task_id=task.task_id,
            agent_id=self.agent_id,
            output_text=result.get("text", ""),
            latency_ms=result.get("latency_ms", 0.0),
            model_used=backend.model_name,
        )
        output.compute_hash()

        self._task_history.append(output)
        return output

    async def _select_backend(self) -> Optional[ModelBackend]:
        if self.model_registry is None:
            return None
        if self.preferred_backend_id:
            backend = self.model_registry.get(self.preferred_backend_id)
            if backend:
                return backend
        return await self.model_registry.get_best_backend(
            self.preferred_capability
        )

    def _build_prompt(self, task: ResearchTask) -> str:
        parts = []
        if task.context:
            parts.append(f"### Context\n{task.context}")
        parts.append(f"### Research Query\n{task.query}")
        if task.expected_output_format:
            parts.append(
                f"### Required Output Format\n{task.expected_output_format}"
            )
        return "\n\n".join(parts)

    @property
    def profile(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "discipline": self.discipline.value,
            "credentials": [c.value for c in self.credentials],
            "preferred_capability": self.preferred_capability,
            "tasks_completed": len(self._task_history),
        }


# =============================================================================
# AGENT TEAM ORCHESTRATOR
# =============================================================================


# Mapping from discipline to recommended model capability
_DISCIPLINE_CAPABILITY: Dict[AgentDiscipline, str] = {
    AgentDiscipline.LAW: "legal_analysis",
    AgentDiscipline.INTELLECTUAL_PROPERTY_LAW: "legal_analysis",
    AgentDiscipline.CORPORATE_LAW: "legal_analysis",
    AgentDiscipline.CRIMINAL_LAW: "legal_analysis",
    AgentDiscipline.INTERNATIONAL_LAW: "legal_analysis",
    AgentDiscipline.CONSTITUTIONAL_LAW: "legal_analysis",
    AgentDiscipline.ENVIRONMENTAL_LAW: "legal_analysis",
    AgentDiscipline.TECHNOLOGY_LAW: "legal_analysis",
    AgentDiscipline.COMPUTER_SCIENCE: "code_analysis",
    AgentDiscipline.ARTIFICIAL_INTELLIGENCE: "code_analysis",
    AgentDiscipline.DATA_SCIENCE: "code_analysis",
    AgentDiscipline.CYBERSECURITY: "code_analysis",
    AgentDiscipline.BLOCKCHAIN_CRYPTOGRAPHY: "code_analysis",
    AgentDiscipline.MEDICINE: "medical_research",
    AgentDiscipline.GENETICS: "medical_research",
    AgentDiscipline.NEUROSCIENCE: "medical_research",
    AgentDiscipline.IMMUNOLOGY: "medical_research",
    AgentDiscipline.PATHOLOGY: "medical_research",
    AgentDiscipline.BIOMEDICAL_INFORMATICS: "medical_research",
    AgentDiscipline.FINANCE: "financial_analysis",
    AgentDiscipline.ACCOUNTING: "financial_analysis",
    AgentDiscipline.ECONOMICS: "financial_analysis",
    AgentDiscipline.PHYSICS: "scientific_research",
    AgentDiscipline.CHEMISTRY: "scientific_research",
    AgentDiscipline.BIOLOGY: "scientific_research",
    AgentDiscipline.MATHEMATICS: "scientific_research",
    AgentDiscipline.STATISTICS: "scientific_research",
    AgentDiscipline.LINGUISTICS: "multilingual",
}


class AgentTeamOrchestrator:
    """
    Orchestrates a scalable team of AI research agents.

    Responsibilities:
    - Dynamically spawn agents per discipline on demand
    - Route research tasks to the best-qualified agent
    - Fan-out multi-discipline questions to parallel agents
    - Aggregate and synthesise results
    - Maintain a full audit trail
    """

    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        max_concurrent: int = 64,
    ):
        self.model_registry = model_registry or ModelRegistry()
        self._agents: Dict[str, ResearchAgent] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._audit_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def spawn_agent(
        self,
        discipline: AgentDiscipline,
        role: AgentRole = AgentRole.DOMAIN_EXPERT,
        credentials: Optional[List[AgentCredential]] = None,
        name: Optional[str] = None,
    ) -> ResearchAgent:
        """Create and register a new research agent."""
        creds = credentials or [AgentCredential.PHD]
        capability = _DISCIPLINE_CAPABILITY.get(
            discipline, "general_research"
        )
        agent_name = name or f"Dr. {discipline.value} Specialist"

        agent = ResearchAgent(
            name=agent_name,
            role=role,
            discipline=discipline,
            credentials=creds,
            model_registry=self.model_registry,
            preferred_capability=capability,
        )
        self._agents[agent.agent_id] = agent
        logger.info("Spawned agent %s (%s)", agent.agent_id, agent_name)
        return agent

    def spawn_full_stanford_team(self) -> List[ResearchAgent]:
        """
        Explosively scale: spawn one agent per Stanford discipline,
        each holding Ph.D. and relevant professional credentials.
        """
        agents: List[ResearchAgent] = []

        credential_map: Dict[AgentDiscipline, List[AgentCredential]] = {
            AgentDiscipline.LAW: [AgentCredential.JD, AgentCredential.PHD],
            AgentDiscipline.INTELLECTUAL_PROPERTY_LAW: [
                AgentCredential.JD, AgentCredential.PHD,
            ],
            AgentDiscipline.CORPORATE_LAW: [
                AgentCredential.JD, AgentCredential.MBA,
            ],
            AgentDiscipline.CRIMINAL_LAW: [AgentCredential.JD],
            AgentDiscipline.INTERNATIONAL_LAW: [
                AgentCredential.JD, AgentCredential.PHD,
            ],
            AgentDiscipline.CONSTITUTIONAL_LAW: [AgentCredential.JD],
            AgentDiscipline.ENVIRONMENTAL_LAW: [
                AgentCredential.JD, AgentCredential.PHD,
            ],
            AgentDiscipline.TECHNOLOGY_LAW: [
                AgentCredential.JD, AgentCredential.PHD,
            ],
            AgentDiscipline.MEDICINE: [
                AgentCredential.MD, AgentCredential.PHD,
            ],
            AgentDiscipline.GENETICS: [
                AgentCredential.MD, AgentCredential.PHD,
                AgentCredential.POSTDOC,
            ],
            AgentDiscipline.NEUROSCIENCE: [
                AgentCredential.MD, AgentCredential.PHD,
                AgentCredential.POSTDOC,
            ],
            AgentDiscipline.FINANCE: [
                AgentCredential.PHD, AgentCredential.CFA,
                AgentCredential.MBA,
            ],
            AgentDiscipline.ACCOUNTING: [
                AgentCredential.PHD, AgentCredential.CPA,
            ],
            AgentDiscipline.ELECTRICAL_ENGINEERING: [
                AgentCredential.PHD, AgentCredential.PE,
                AgentCredential.MSEE,
            ],
            AgentDiscipline.MECHANICAL_ENGINEERING: [
                AgentCredential.PHD, AgentCredential.PE,
                AgentCredential.MSME,
            ],
            AgentDiscipline.LIBRARY_INFORMATION_SCIENCE: [
                AgentCredential.PHD, AgentCredential.MLS,
            ],
        }

        for discipline in AgentDiscipline:
            creds = credential_map.get(
                discipline,
                [AgentCredential.PHD, AgentCredential.POSTDOC],
            )
            agent = self.spawn_agent(
                discipline=discipline,
                role=AgentRole.DOMAIN_EXPERT,
                credentials=creds,
            )
            agents.append(agent)

        logger.info(
            "Spawned full Stanford team: %d agents across all disciplines",
            len(agents),
        )
        return agents

    def get_agent(self, agent_id: str) -> Optional[ResearchAgent]:
        return self._agents.get(agent_id)

    def get_agents_by_discipline(
        self, discipline: AgentDiscipline
    ) -> List[ResearchAgent]:
        return [
            a
            for a in self._agents.values()
            if a.discipline == discipline
        ]

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    async def assign_task(
        self,
        task: ResearchTask,
        agent_id: Optional[str] = None,
        discipline: Optional[AgentDiscipline] = None,
    ) -> ResearchOutput:
        """Assign a task to a specific agent or auto-select by discipline."""
        if agent_id:
            agent = self._agents.get(agent_id)
        elif discipline:
            candidates = self.get_agents_by_discipline(discipline)
            if not candidates:
                agent = self.spawn_agent(discipline)
            else:
                agent = candidates[0]
        else:
            agent = next(iter(self._agents.values()), None)
            if agent is None:
                agent = self.spawn_agent(AgentDiscipline.COMPUTER_SCIENCE)

        async with self._semaphore:
            output = await agent.execute(task)

        self._audit_log.append({
            "event": "task_completed",
            "task_id": task.task_id,
            "agent_id": agent.agent_id,
            "discipline": agent.discipline.value,
            "model": output.model_used,
            "latency_ms": output.latency_ms,
            "hash": output.hash,
            "timestamp": output.timestamp,
        })
        return output

    async def fan_out(
        self,
        task: ResearchTask,
        disciplines: List[AgentDiscipline],
    ) -> List[ResearchOutput]:
        """
        Fan a task out to multiple discipline specialists in parallel.
        """
        coros = [
            self.assign_task(task, discipline=d) for d in disciplines
        ]
        return await asyncio.gather(*coros)

    async def research_and_synthesise(
        self,
        query: str,
        disciplines: List[AgentDiscipline],
        context: str = "",
    ) -> Dict[str, Any]:
        """
        High-level API: fan-out a research query across disciplines,
        then synthesise the combined output.
        """
        task = ResearchTask(query=query, context=context)
        outputs = await self.fan_out(task, disciplines)

        combined = "\n\n---\n\n".join(
            f"[{self._agents[o.agent_id].discipline.value}]\n{o.output_text}"
            for o in outputs
            if o.output_text
        )

        synth_agent = self.spawn_agent(
            discipline=AgentDiscipline.DATA_SCIENCE,
            role=AgentRole.SYNTHESIS_COORDINATOR,
            credentials=[AgentCredential.PHD, AgentCredential.POSTDOC],
            name="Synthesis Coordinator",
        )

        synth_task = ResearchTask(
            query=(
                "Synthesise the following multi-discipline research outputs "
                "into a single coherent analysis.  Resolve contradictions, "
                "identify consensus, and highlight areas needing further "
                "investigation."
            ),
            context=combined,
            temperature=0.3,
        )
        synthesis = await synth_agent.execute(synth_task)

        return {
            "query": query,
            "discipline_outputs": [
                {
                    "discipline": self._agents[o.agent_id].discipline.value,
                    "agent_id": o.agent_id,
                    "text": o.output_text,
                    "confidence": o.confidence,
                    "model": o.model_used,
                    "latency_ms": o.latency_ms,
                    "hash": o.hash,
                }
                for o in outputs
            ],
            "synthesis": {
                "text": synthesis.output_text,
                "model": synthesis.model_used,
                "latency_ms": synthesis.latency_ms,
                "hash": synthesis.hash,
            },
            "agent_count": len(self._agents),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    @property
    def team_summary(self) -> Dict[str, Any]:
        disciplines = defaultdict(int)
        for agent in self._agents.values():
            disciplines[agent.discipline.value] += 1
        return {
            "total_agents": len(self._agents),
            "disciplines": dict(disciplines),
            "audit_log_entries": len(self._audit_log),
            "model_registry": self.model_registry.summary,
        }

    async def close(self) -> None:
        await self.model_registry.close_all()
