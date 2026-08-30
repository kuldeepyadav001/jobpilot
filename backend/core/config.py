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
    search_keywords: str = "python developer, react developer"
    # How many highest-scoring jobs to target per apply cycle.
    apply_target_count: int = 10

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore", env_prefix="")


settings = Settings()