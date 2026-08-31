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


def calculate_keyword_coverage(tags: List[str], jd_text: str, denominator_cap: int = 10) -> float:
    """Calculates direct keyword match percentage.

    If a job description mentions 6 out of 10 tags, coverage is 60.0%.

    `denominator_cap` prevents a *generalist* resume (many tags) from being
    unfairly penalized: a real JD only tests a subset of all the skills a broad
    resume lists, so coverage is measured against the most relevant `cap` skills
    rather than every listed tag. Specialty resumes with few tags are unaffected
    because min(len(tags), cap) == len(tags) for them.
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

    effective_denominator = min(len(tags), max(1, denominator_cap))
    coverage = (min(matched_count, effective_denominator) / effective_denominator) * 100.0
    return round(coverage, 2)


# Role-family words map to the skill tags a resume in that family would carry.
# Used so Internshala-style titles ("Backend Development", "Machine Learning")
# honestly boost the matching resume even though the title isn't a literal skill list.
_ROLE_FAMILIES = {
    "backend": ["python", "java", "node", "go", "golang", "django", "flask", "fastapi",
                "spring", "sql", "postgresql", "rest api", "apis", "redis"],
    "frontend": ["react", "javascript", "typescript", "html", "css", "angular",
                 "vue", "next.js", "ui", "ux"],
    "full stack": ["python", "react", "javascript", "node", "java", "sql", "html",
                   "css", "django", "fastapi"],
    "developer": ["python", "java", "javascript", "react", "sql", "git", "api"],
    "devops": ["docker", "kubernetes", "aws", "terraform", "ci/cd", "linux", "jenkins"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux"],
    "data": ["python", "sql", "pandas", "numpy", "power bi", "excel", "tableau", "etl"],
    "data science": ["python", "pandas", "numpy", "machine learning", "scikit", "sql"],
    "machine learning": ["python", "machine learning", "tensorflow", "pytorch", "nlp",
                         "sklearn", "deep learning"],
    "ai": ["python", "machine learning", "nlp", "tensorflow", "pytorch", "llm", "ai"],
    "web": ["python", "react", "javascript", "html", "css", "django", "node"],
    "testing": ["pytest", "selenium", "automation", "qa", "python"],
}


def _title_relevance(title: str, tags: List[str], max_bonus: float = 18.0, cap: int = 5) -> float:
    """Bounded role-title / role-family relevance.

    Internshala internship titles are concise ROLE names (e.g. "Backend
    Development", "Machine Learning") — strong, real relevance signal that a thin
    generic job description can drown out. We add a bounded bonus (up to
    `max_bonus`) from two sources:
      * literal skill-tag matches in the title, and
      * role-family overlaps (the title names a family the resume belongs to).
    Capped so an irrelevant title can never push a bad match high.
    """
    if not title or not tags:
        return 0.0
    ct = clean_text(title)
    if not ct:
        return 0.0

    # Source A: literal skill tags appearing in the title.
    matched = 0
    for tag in tags:
        ctg = clean_text(tag)
        if ctg and re.search(r"\b" + re.escape(ctg) + r"\b", ct):
            matched += 1
    literal = min(matched, cap) / cap

    # Source B: role-family overlap (title names a family the resume belongs to).
    tag_set = {clean_text(t) for t in tags if clean_text(t)}
    family_hits = 0
    for family, family_tags in _ROLE_FAMILIES.items():
        if re.search(r"\b" + re.escape(family) + r"\b", ct):
            # This family is named in the title; does the resume carry it?
            overlap = any(clean_text(ft) in tag_set or ft in tag_set for ft in family_tags)
            if overlap:
                family_hits += 1
    family = min(family_hits, 3) / 3

    relevant = max(literal, family)
    return round(relevant * max_bonus, 2)


def compute_hybrid_match_score(resume: Resume, job_description: str,
                               title: str = "", job_type: str = "job") -> float:
    """
    Combines Keyword Coverage + TF-IDF Contextual Similarity + a bounded
    role-title term. Produces realistic ATS scores in the 30% - 95% range.

    `title`/`job_type` are optional; when omitted the title term contributes 0 so
    existing (job-oriented) callers are unchanged.
    """
    cleaned_jd = clean_text(job_description)
    if not cleaned_jd:
        return 0.0

    # 1. Direct Keyword Coverage (Tags) — generalist-breadth proof (cap=10)
    tags = resume.tags if isinstance(resume.tags, list) else []
    coverage_score = calculate_keyword_coverage(tags, cleaned_jd, denominator_cap=10)

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

    # 3. Weighted Final Score.
    # TF-IDF is the stronger, model-free signal of real relevance, so it now gets
    # more weight (45%) than before. Keyword coverage (55%) confirms hard-skill
    # presence. Rebalancing lifts well-matched jobs into a full ~70-95 range while
    # keeping the ranking honest.
    if tags:
        final_score = (coverage_score * 0.55) + (tfidf_score * 0.45)
    else:
        final_score = tfidf_score

    # 4. Bounded role-title relevance (mostly helps internships, whose concise
    # titles carry real signal but whose JDs are diluted with boilerplate). It only
    # applies when a title is supplied and can never push an irrelevant match high.
    if title:
        final_score += _title_relevance(title, tags)

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


def select_best_resume(job_description: str, resumes: List[Resume],
                       title: str = "", job_type: str = "job") -> Tuple[Optional[Resume], float]:
    """
    Evaluates all active resumes against a job description.
    Returns the highest-scoring (Resume, score) tuple. `title`/`job_type` are
    forwarded to the scorer so internships get a fair, bounded title-relevance term.
    """
    best_resume: Optional[Resume] = None
    highest_score: float = -1.0

    for resume in resumes:
        if not resume.is_active:
            continue

        score = compute_hybrid_match_score(resume, job_description, title=title, job_type=job_type)
        if score > highest_score:
            highest_score = score
            best_resume = resume

    return best_resume, max(highest_score, 0.0)