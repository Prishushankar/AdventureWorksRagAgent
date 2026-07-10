import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    groq_api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    db_server: str = field(default_factory=lambda: os.environ.get("DB_SERVER", "localhost"))
    db_database: str = field(default_factory=lambda: os.environ.get("DB_DATABASE", "AdventureWorks2022"))
    db_trusted_connection: str = field(default_factory=lambda: os.environ.get("DB_TRUSTED_CONNECTION", "yes"))
    db_encrypt: str = field(default_factory=lambda: os.environ.get("DB_ENCRYPT", "no"))
    schema_yaml_path: str = field(default_factory=lambda: os.environ.get("SCHEMA_YAML_PATH", "config/schema_adventureworks.yaml"))
    chroma_db_path: str = field(default_factory=lambda: os.environ.get("CHROMA_DB_PATH", "./chroma_db"))
    embedding_model: str = field(default_factory=lambda: os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5"))
    llm_model: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", "llama-3.1-8b-instant"))
    explanation_model: str = field(default_factory=lambda: os.environ.get("EXPLANATION_MODEL", "llama-3.3-70b-versatile"))
    retrieval_top_k: int = field(default_factory=lambda: int(os.environ.get("RETRIEVAL_TOP_K", "10")))
    escalation_distance_threshold: float = field(default_factory=lambda: float(os.environ.get("ESCALATION_DISTANCE_THRESHOLD", "0.65")))
    rerank_top_k: int = field(default_factory=lambda: int(os.environ.get("RERANK_TOP_K", "5")))
    query_expansion_count: int = field(default_factory=lambda: int(os.environ.get("QUERY_EXPANSION_COUNT", "3")))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    @property
    def connection_string(self) -> str:
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.db_server};"
            f"DATABASE={self.db_database};"
            f"Trusted_Connection={self.db_trusted_connection};"
            f"Encrypt={self.db_encrypt};"
        )

    def validate(self) -> None:
        missing: list[str] = []
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if missing:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing)}. Set them in .env file.")


config = Config()
