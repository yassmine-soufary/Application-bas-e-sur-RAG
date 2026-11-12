from pathlib import Path
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / 'backend/.env', extra='ignore')
    openai_api_key: SecretStr = SecretStr('')
    openai_model: str = 'gpt-4.1-mini'
    openai_embedding_model: str = 'text-embedding-3-small'
    chroma_path: str = '../data/chroma_db'
    top_k_default: int = Field(5, ge=1, le=30)
    similarity_threshold: float = Field(0.5, ge=-1, le=1)
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']

    @field_validator('openai_model', 'openai_embedding_model')
    @classmethod
    def model_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Le modèle ne peut pas être vide.')
        return value.strip()

    @property
    def db_path(self) -> Path:
        path = Path(self.chroma_path)
        return path if path.is_absolute() else (ROOT / 'backend' / path).resolve()
