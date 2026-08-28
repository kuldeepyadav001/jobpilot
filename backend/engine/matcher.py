import re
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
from models.resume import Resume


def clean_text(text: str) -> str:
    """Normalizes text by removing non-alphanumeric noise and extra spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_match_score(resume_text: str, job_description: str) -> float:
    """
    Computes cosine similarity percentage (0.0 to 100.0)
    between a resume and job description using TF-IDF.
    """
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(job_description)

    if not cleaned_resume or not cleaned_jd:
        return 0.0

    try:
        # max_df=1.0 ensures terms present in both documents are NOT stripped
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=1.0,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(similarity) * 100, 2)
    except Exception as e:
        logger.error(f"Error computing match score: {e}")
        return 0.0


def select_best_resume(job_description: str, resumes: List[Resume]) -> Tuple[Optional[Resume], float]:
    """
    Evaluates all active resumes against a job description.
    Returns the highest-scoring (Resume, score) tuple.
    """
    best_resume: Optional[Resume] = None
    highest_score: float = -1.0

    for resume in resumes:
        if not resume.is_active or not resume.parsed_text:
            continue

        score = compute_match_score(resume.parsed_text, job_description)
        if score > highest_score:
            highest_score = score
            best_resume = resume

    return best_resume, max(highest_score, 0.0)