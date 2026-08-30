from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # App
    environment: str = "development"
    secret_key: str

    # Email
    email_address: str = ""
    email_app_password: str = ""
    imap_server: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:1.5b"

    # Candidate identity — used in cover-letter signatures. Never hardcode personal data.
    candidate_name: str = ""

    # APPLY GATE (how "one click, everything done" behaves)
    #   apply_mode = 'real'     -> manual run REALLY submits applications (email/portal)
    #   apply_mode = 'dry_run'  -> manual run does everything EXCEPT the final submit (safe)
    apply_mode: str = "dry_run"
    #   auto_apply = true       -> the scheduled 6-hourly run ALSO submits applications
    #   auto_apply = false      -> scheduled run only scrapes+serves+scores+scans; never applies.
    #                              (Recommended: keep false; you trigger applies yourself.)
    auto_apply: bool = False

    # Scraping
    # match_score_threshold is now a soft FLOOR: jobs scoring below this are skipped.
    # Leave at 0 to disable the floor and apply to the top-N instead (recommended while
    # the score scale is uncalibrated). A too-high value quietly blocks all applies.
    match_score_threshold: int = 0
    scheduler_interval_hours: int = 6
    # Broad keywords: cast a wide net across the user's resume roles.
    search_keywords: str = (
        "python developer, backend developer, full stack developer, java developer, "
        "frontend developer, react developer, machine learning, ai engineer, "
        "devops engineer, cloud engineer"
    )
    # How many highest-scoring jobs to target per apply cycle.
    apply_target_count: int = 10
    # Where to scrape (used by the pipeline; overrides the old hardcoded "remote").
    search_location: str = "remote"
    # How many cards to pull per portal per keyword in one scrape cycle.
    max_per_portal: int = 5

    # JOB CLEANUP: prune stale, never-applied jobs automatically so the DB doesn't
    # fill up. Jobs older than job_retention_days that were never applied (and not
    # referenced by any application) are removed each week.
    job_cleanup_enabled: bool = True
    job_retention_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore", env_prefix="")


settings = Settings()