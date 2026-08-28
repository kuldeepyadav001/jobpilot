from typing import Optional
from loguru import logger
from ai.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are an expert career consultant and professional resume writer.
Your job is to write a concise, compelling, and tailored cover letter (maximum 180-220 words) for a job application.
Highlight matching technical skills directly relevant to the job requirements without fluff, exaggeration, or clichés."""


def build_template_fallback(job_title: str, company_name: str, skills_summary: str) -> str:
    """Deterministic fallback if local LLM service is offline."""
    return (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am writing to express my strong interest in the {job_title} role. "
        f"My background and technical experience in {skills_summary} align closely with the qualifications needed for this position.\n\n"
        f"I have hands-on experience building clean, maintainable systems and working with modern engineering workflows. "
        f"I look forward to the opportunity to contribute to your team.\n\n"
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,\nApplicant"
    )


async def generate_tailored_cover_letter(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_text: str
) -> str:
    """
    Generates a tailored cover letter using Ollama.
    Falls back to a structured template if Ollama is unreachable.
    """
    prompt = f"""
Write a targeted, concise cover letter for this position:
- Target Job Title: {job_title}
- Target Company: {company_name}
- Job Description / Requirements:
{job_description[:1000]}

Candidate Resume Text:
{resume_text[:1200]}

Requirements:
- Keep length under 200 words.
- Professional, direct, and enthusiastic tone.
- Reference 2-3 specific technical matches.
- Do not invent experience not present in the resume.
"""

    client = OllamaClient()
    logger.info(f"[AI Layer] Generating cover letter for {job_title} at {company_name}...")
    ai_generated = await client.generate_text(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    if ai_generated:
        logger.info("[AI Layer] Cover letter generated successfully via Ollama.")
        return ai_generated

    # Graceful degradation fallback
    logger.warning("[AI Layer] Falling back to structured deterministic template.")
    return build_template_fallback(
        job_title=job_title,
        company_name=company_name,
        skills_summary="Python, FastAPI, SQL, and backend system architecture"
    )