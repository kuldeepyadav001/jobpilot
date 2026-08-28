from pydantic_settings import BaseSettings


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
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5:1.5b"

    # Scraping
    match_score_threshold: int = 65
    scheduler_interval_hours: int = 6

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()