import re
from typing import List, Tuple, Optional, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
from models.resume import Resume


def clean_text(text: str) -> str:
    """Normalizes text by lowercasing and standardizing characters."""
    if not text:
        return ""
    text = text.lower()
    # Retain tech symbols like c++, c#, .net, node.js
    text = re.sub(r"[^a-z0-9\s#+.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def calculate_keyword_coverage(tags: List[str], jd_text: str) -> float:
    """
    Calculates direct keyword match percentage.
    If a job description mentions 6 out of 10 tags, coverage is 60.0%.
    """
    if not tags or not jd_text:
        return 0.0

    cleaned_jd = clean_text(jd_text)
    matched_count = 0

    for tag in tags:
        clean_tag = clean_text(tag)
        if not clean_tag:
            continue
        pattern = r"\b" + re.escape(clean_tag) + r"\b"
        if re.search(pattern, cleaned_jd):
            matched_count += 1

    coverage = (matched_count / len(tags)) * 100.0
    return round(coverage, 2)


def compute_hybrid_match_score(resume: Resume, job_description: str) -> float:
    """
    Combines Keyword Coverage (70%) + TF-IDF Contextual Similarity (30%).
    Produces realistic ATS scores in the 30% - 90% range.
    """
    cleaned_jd = clean_text(job_description)
    if not cleaned_jd:
        return 0.0

    # 1. Direct Keyword Coverage (Tags)
    tags = resume.tags if isinstance(resume.tags, list) else []
    coverage_score = calculate_keyword_coverage(tags, cleaned_jd)

    # 2. Contextual TF-IDF Similarity
    resume_text = clean_text(resume.parsed_text or " ".join(tags))
    tfidf_score = 0.0

    if resume_text:
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_df=1.0,
                min_df=1
            )
            matrix = vectorizer.fit_transform([resume_text, cleaned_jd])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            # Scale TF-IDF cosine (0.05 - 0.25) by 300 to match percentage scale
            tfidf_score = min(sim * 300.0, 100.0)
        except Exception as e:
            logger.debug(f"TF-IDF calculation fallback: {e}")
            tfidf_score = 0.0

    # 3. Weighted Final Score
    if tags:
        final_score = (coverage_score * 0.70) + (tfidf_score * 0.30)
    else:
        final_score = tfidf_score

    return round(min(final_score, 100.0), 2)


def compute_match_score(resume_input: Union[Resume, str], job_description: str) -> float:
    """
    Backward-compatible wrapper. Handles both a Resume model instance or raw string.
    """
    if isinstance(resume_input, Resume):
        return compute_hybrid_match_score(resume_input, job_description)

    # If raw string is passed, calculate pure TF-IDF cosine
    cleaned_res = clean_text(str(resume_input))
    cleaned_jd = clean_text(job_description)
    if not cleaned_res or not cleaned_jd:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_df=1.0, min_df=1)
        matrix = vectorizer.fit_transform([cleaned_res, cleaned_jd])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(min(sim * 300.0, 100.0)), 2)
    except Exception:
        return 0.0


def select_best_resume(job_description: str, resumes: List[Resume]) -> Tuple[Optional[Resume], float]:
    """
    Evaluates all active resumes against a job description.
    Returns the highest-scoring (Resume, score) tuple.
    """
    best_resume: Optional[Resume] = None
    highest_score: float = -1.0

    for resume in resumes:
        if not resume.is_active:
            continue

        score = compute_hybrid_match_score(resume, job_description)
        if score > highest_score:
            highest_score = score
            best_resume = resume

    return best_resume, max(highest_score, 0.0)