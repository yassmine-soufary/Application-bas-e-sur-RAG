from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class IngestRequest(BaseModel):
    strategy: Literal['fixed', 'structural'] = 'structural'
    chunk_size: int = Field(500, gt=0, le=12000)
    overlap: int = Field(100, ge=0)

    @model_validator(mode='after')
    def valid_overlap(self):
        if self.overlap >= self.chunk_size:
            raise ValueError('overlap doit être strictement inférieur à chunk_size')
        return self


class Filters(BaseModel):
    type: str | None = None


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(None, ge=1, le=30)
    filters: Filters = Field(default_factory=Filters)

    @field_validator('question')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('La question ne peut pas être vide.')
        return value.strip()


class Chunk(BaseModel):
    id: str
    file: str
    reference: str
    type: str
    date: str
    version: str = ''
    status: str = ''
    page: int = Field(ge=1)
    section: str
    text: str


class Source(BaseModel):
    id: int
    chunk_id: str
    file: str
    reference: str
    date: str
    page: int
    section: str
    excerpt: str
    score: float


class SearchHit(BaseModel):
    chunk: Chunk
    score: float


class SearchResponse(BaseModel):
    hits: list[SearchHit]


class AskResponse(BaseModel):
    answer: str
    found: bool
    sources: list[Source] = []
    invalid_citations: list[int] = []
    latency_ms: int


class DocumentInfo(BaseModel):
    file: str
    reference: str
    type: str
    date: str
    version: str
    status: str
    chunks: int


class HealthResponse(BaseModel):
    server: str = 'ok'
    chroma: str = 'ok'
    chunks: int
    openai_configured: bool


class IngestResponse(BaseModel):
    collection: str
    chunks: int
    reused: bool
