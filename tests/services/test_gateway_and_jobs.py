from __future__ import annotations

import pytest

from job_runtime import InMemoryJobRunner, JobStatus, JobSubmission
from llm_gateway import LLMGateway, NullLLMProvider
from llm_gateway.ports import LLMCompletionRequest, LLMProviderName
from prompts import PromptRegistry, PromptTemplate


@pytest.mark.asyncio
async def test_null_llm_gateway_tracks_usage() -> None:
    gateway = LLMGateway(
        providers={LLMProviderName.NULL: NullLLMProvider()},
        role_routing={"SYNTHESIS": LLMProviderName.NULL},
    )
    response = await gateway.complete(
        LLMCompletionRequest(
            organisation_id="org-1",
            role="SYNTHESIS",
            template_id="think.synthesis",
            messages=[{"role": "user", "content": "hello"}],
        )
    )
    assert response.provider == LLMProviderName.NULL
    assert "structured_summary" in response.__dataclass_fields__
    assert response.usage.total_tokens > 0


def test_job_runner_memory_backend() -> None:
    runner = InMemoryJobRunner()
    runner.register("peacock.ping", lambda payload: {"echo": payload["x"]})
    handle = runner.enqueue(
        JobSubmission(
            name="peacock.ping",
            organisation_id="org-1",
            payload={"x": 1},
        )
    )
    assert handle.status == JobStatus.SUCCEEDED
    assert handle.result == {"echo": 1}


def test_prompt_registry_is_provider_agnostic() -> None:
    registry = PromptRegistry(
        [
            PromptTemplate(
                template_id="think.synthesis",
                role="SYNTHESIS",
                system="Synthesize evidence",
                user="Summarize {{topic}}",
            )
        ]
    )
    template = registry.get("think.synthesis")
    assert template.role == "SYNTHESIS"
