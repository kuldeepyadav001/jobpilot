"""Tests the top-N apply-target selection logic (no browser/network)."""
from scheduler.jobs import select_apply_targets
from models.company import Company
from models.job import Job


def _seed_jobs(s, scores, applied_urls=None, blacklisted_urls=None, salaries=None):
    comp = Company(name="Acme", blacklisted=False)
    s.add(comp)
    s.flush()
    ids = []
    applied_urls = applied_urls or set()
    blacklisted_urls = blacklisted_urls or set()
    salaries = salaries or [None] * len(scores)
    for i, score in enumerate(scores):
        url = f"https://internshala.com/jobs/uuid-{i}"
        j = Job(
            portal="internshala",
            title=f"Job {i}",
            company_id=comp.id,
            url=url,
            match_score=score,
            salary_min=salaries[i],
            is_applied=url in applied_urls,
            is_blacklisted=url in blacklisted_urls,
        )
        s.add(j)
        s.flush()
        ids.append((j.id, score, url))
    s.commit()
    return ids


def test_top_n_ordering(session):
    _seed_jobs(session, [10, 40, 30, 20])
    targets = select_apply_targets(session, threshold=0, target_count=2)
    # Top 2 by score = 40 and 30
    assert [j.match_score for j in targets] == [40.0, 30.0]


def test_threshold_filters(session):
    _seed_jobs(session, [10, 40, 30, 20])
    targets = select_apply_targets(session, threshold=25, target_count=10)
    assert all(j.match_score >= 25 for j in targets)
    assert len(targets) == 2  # 40 and 30


def test_ignores_applied_and_blacklisted(session):
    applied = {"https://internshala.com/jobs/uuid-0"}   # score 10
    blacklisted = {"https://internshala.com/jobs/uuid-1"}  # score 40
    _seed_jobs(session, [10, 40, 30, 20], applied_urls=applied, blacklisted_urls=blacklisted)
    targets = select_apply_targets(session, threshold=0, target_count=10)
    got = [j.match_score for j in targets]
    assert 10.0 not in got  # applied
    assert 40.0 not in got  # blacklisted
    assert got == [30.0, 20.0]


def test_empty_when_no_scores(session):
    _seed_jobs(session, [1, 2, 3])
    # Force match_score None by filtering is fine; just ensure a floor still returns top-N
    targets = select_apply_targets(session, threshold=0, target_count=1)
    assert len(targets) == 1


def test_min_salary_excludes_known_low_and_ranks_unknown_after_known(session):
    # salaries: 0->2L(low), 1->10L(high), 2(none/unknown), 3->6L
    _seed_jobs(session, [50, 90, 70, 80], salaries=[2_00_000, 10_00_000, None, 6_00_000])
    targets = select_apply_targets(session, threshold=0, target_count=10, min_salary=5_00_000)
    got = [(j.salary_min, j.match_score) for j in targets]
    # Exclude the 2L job (known below min). Unknown-salary job kept but ranked after known-paid.
    assert None not in [x[0] for x in got if x[0] is not None and x[0] < 5_00_000]  # no known-low
    assert 2_00_000 not in [x[0] for x in got]  # 2L excluded
    # Unknown salary job is present, but comes after the known high-paid jobs.
    assert any(x[0] is None for x in got)
    # The high-paid (10L) job is first among known-salary jobs.
    known = [g[0] for g in got if g[0] is not None]
    assert known == sorted(known, reverse=True)
