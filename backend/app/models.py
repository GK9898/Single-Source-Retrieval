from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# --- Upload Models ---
class UploadResponse(BaseModel):
    filename: str
    document_id: str
    num_chunks: int
    num_pages: int
    status: str
    message: str


# --- Query Models ---
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query string")
    document_id: Optional[str] = Field(None, description="Optional target document ID")
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = Field(default=True)


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    score: float
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceChunk]
    execution_time_ms: float
    document_id: Optional[str] = None
    query_type: Optional[str] = "single_fact"
    sub_queries: List[str] = []



# --- Suggestions Models ---
class SuggestionsRequest(BaseModel):
    context: Optional[str] = None
    document_id: Optional[str] = None
    num_suggestions: int = Field(default=3, ge=1, le=10)


class SuggestionsResponse(BaseModel):
    suggestions: List[str]


# --- Topics Models ---
class TopicsRequest(BaseModel):
    document_id: Optional[str] = None
    max_topics: int = Field(default=5, ge=1, le=20)


class TopicItem(BaseModel):
    topic: str
    relevance_score: float
    summary: Optional[str] = None


class TopicsResponse(BaseModel):
    document_id: Optional[str] = None
    topics: List[TopicItem]


# --- TTS Models ---
class TTSRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    voice: Optional[str] = "en-US-Standard-A"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TTSResponse(BaseModel):
    audio_base64: str
    format: str = "mp3"
    duration_seconds: float


# --- Evaluate Models ---
class EvaluateRequest(BaseModel):
    query: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None


class EvaluateMetrics(BaseModel):
    faithfulness: float
    answer_relevance: float
    context_recall: float
    context_precision: float
    overall_score: float


class EvaluateResponse(BaseModel):
    metrics: EvaluateMetrics
    evaluated_at: str
    log_file: str
