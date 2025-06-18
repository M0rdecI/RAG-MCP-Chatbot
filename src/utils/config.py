from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Dict, Optional
from pathlib import Path

class ChatbotConfig(BaseSettings):
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # LLM Settings
    llm_model: str = Field(default="qwen2:7b", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    
    # Vector Store Settings
    vector_store_path: Path = Field(default=Path("data/vector_store"))
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    
    # Storage Settings
    chat_history_path: Path = Field(default=Path("data/chat_history"))
    document_path: Path = Field(default=Path("data/documents"))
    
    # API Security
    api_key: str = Field(default="your-secret-api-key", env="API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

config = ChatbotConfig()