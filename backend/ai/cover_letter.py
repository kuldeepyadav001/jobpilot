import re
from loguru import logger
from ai.ollama_client import OllamaClient
from core.config import settings
SYSTEM_PROMPT = """You are an expert recruiter and elite resume writer.
Your job is to write a highly tailored, direct, and compelling email cover letter (maximum 150 words).

CRITICAL FORMATTING RULES:
1. NEVER include physical headers, addresses, phone numbers, emails, or dates at the top.
2. Start DIRECTLY with the greeting: 'Dear Hiring Team at [Company Name],' or 'Dear [Company Name] Team,'.
3. End cleanly with: 'Best regards,\n[Candidate Name]' (Replace [Candidate Name] with the actual candidate's name from the resume).
4. NEVER use bracketed placeholders like [University], [Address], [Today's Date], [Recipient's Name], or [Date].
5. If the resume does not specify a detail (like university name), speak generally: 'my university' or 'my technical program', never leave a placeholder."""


async def generate_tailored_cover_letter(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_text: str
) -> str:
    """
    Generates a tailored, placeholder-free cover letter using Ollama.
    """
    # Candidate name: prefer the configured setting, else derive from the resume's first line.
    candidate_name = (settings.candidate_name or "").strip()
    first_line = resume_text.strip().split("\n")[0].strip()
    if not candidate_name and len(first_line) < 50 and any(char.isalpha() for char in first_line):
        candidate_name = first_line
    candidate_name = candidate_name or "the applicant"

    prompt = f"""
Write a direct, professional email cover letter for this job:
- Job Title: {job_title}
- Company: {company_name}
- Job Description:
{job_description[:800]}

Candidate Resume/Skills:
{resume_text[:1200]}

CRITICAL: 
- Keep it under 130 words.
- Start directly with the greeting. No headers.
- Match candidate's skills directly to the role requirements.
- Use the candidate name: {candidate_name} at the bottom.
- Zero placeholders.
"""

    client = OllamaClient()
    logger.info(f"[AI Layer] Generating cover letter for {job_title} at {company_name}...")
    ai_generated = await client.generate_text(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    if ai_generated:
        # Final safety filter: clean up any accidental brackets the LLM generated
        clean_cl = re.sub(r"\[.*?\]", "", ai_generated)
        logger.info("[AI Layer] Cover letter generated successfully via Ollama.")
        return clean_cl.strip()

    # Fallback
    logger.warning("[AI Layer] Falling back to structured deterministic template.")
    return (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am writing to express my strong interest in the {job_title} position. "
        f"My background in full-stack software engineering and hands-on experience "
        f"building clean, scalable backend systems align closely with your team's needs.\n\n"
        f"I am proficient in modern engineering workflows, backend architecture, and rapid deployment. "
        f"I look forward to the possibility of discussing how I can contribute to your team.\n\n"
        f"Best regards,\n{candidate_name}"
    )