"""Tests for cover-letter generation fallback + candidate-name resolution.

Forces the Ollama path to fail so we exercise the deterministic template and
verify no hardcoded personal name leaks into the output.
"""
import pytest
from ai import cover_letter as cl_mod
from core.config import settings


@pytest.mark.asyncio
async def test_fallback_template_uses_resume_name(monkeypatch):
    async def _fail(self, prompt, system_prompt=None):
        return None
    monkeypatch.setattr(cl_mod.OllamaClient, "generate_text", _fail)
    monkeypatch.setattr(settings, "candidate_name", "")

    text = await cl_mod.generate_tailored_cover_letter(
        job_title="Python Developer",
        company_name="Acme",
        job_description="Build with Python and FastAPI.",
        resume_text="Jane Candidate\nPython backend engineer.",
    )
    assert "Dear Hiring Team at Acme" in text
    assert "Jane Candidate" in text
    # Must not contain any hardcoded personal name from the old code.
    assert "kuldeep" not in text.lower()


@pytest.mark.asyncio
async def test_fallback_template_prefers_configured_name(monkeypatch):
    async def _fail(self, prompt, system_prompt=None):
        return None
    monkeypatch.setattr(cl_mod.OllamaClient, "generate_text", _fail)
    monkeypatch.setattr(settings, "candidate_name", "Alex Doe")

    text = await cl_mod.generate_tailored_cover_letter(
        job_title="Backend Engineer",
        company_name="Beta",
        job_description="Backend work.",
        resume_text="Ignored First Line\n...",
    )
    assert "Alex Doe" in text
    assert "Ignored First Line" not in text
