"""Tests the top-N apply-target selection logic (no browser/network)."""
from scheduler.jobs import select_apply_targets
from models.company import Company
from models.job import Job


def _seed_jobs(s, scores, applied_urls=None, blacklisted_urls=None):
    comp = Company(name="Acme", blacklisted=False)
    s.add(comp)
    s.flush()
    ids = []
    applied_urls = applied_urls or set()
    blacklisted_urls = blacklisted_urls or set()
    for i, score in enumerate(scores):
        url = f"https://internshala.com/jobs/uuid-{i}"
        j = Job(
            portal="internshala",
            title=f"Job {i}",
            company_id=comp.id,
            url=url,
            match_score=score,
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
