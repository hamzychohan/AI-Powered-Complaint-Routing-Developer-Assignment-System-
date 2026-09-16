import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    
    VECTOR_DB_TYPE: str = "chroma"
    CHROMA_DB_DIR: str = "./data/chroma_db"
    POSTGRES_CONNECTION_STRING: str = "postgresql://postgres:postgres@localhost:5432/complaint_rag"
    
    JIRA_SERVER_URL: str = ""
    JIRA_USER_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_PROJECT_KEY: str = "COMP"
    
    SQLITE_DB_PATH: str = "./data/audit_logs.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
