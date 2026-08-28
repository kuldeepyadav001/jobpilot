import os
import pdfplumber
import docx
from loguru import logger


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text from a PDF resume."""
    text_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
        return "\n".join(text_content).strip()
    except Exception as e:
        logger.error(f"Failed to parse PDF resume at {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extracts raw text from a DOCX resume."""
    try:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
    except Exception as e:
        logger.error(f"Failed to parse DOCX resume at {file_path}: {e}")
        return ""


def parse_resume_file(file_path: str, file_type: str) -> str:
    """Dispatches parsing based on file extension."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found at: {file_path}")

    ext = file_type.lower().replace(".", "")
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported resume file format: {file_type}")