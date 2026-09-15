export interface SourceChunk {
  chunk_id: string;
  text: string;
  score: number;
  page_number?: number;
  metadata?: Record<string, any>;
}

export interface QueryResponse {
  query: string;
  answer: string;
  sources: SourceChunk[];
  execution_time_ms: number;
  document_id?: string;
  query_type?: string;
  sub_queries?: string[];
}

export interface UploadResponse {
  filename: string;
  document_id: string;
  num_chunks: number;
  num_pages: number;
  status: string;
  message: string;
}

export interface TopicItem {
  topic: string;
  relevance_score: number;
  summary?: string;
}

export interface EvaluateMetrics {
  faithfulness: number;
  answer_relevance: number;
  context_recall: number;
  context_precision: number;
  overall_score: number;
}

export interface EvaluateResponse {
  metrics: EvaluateMetrics;
  evaluated_at: string;
  log_file: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  sources?: SourceChunk[];
  executionTime?: number;
  evaluation?: EvaluateMetrics;
  queryType?: string;
  subQueries?: string[];
}

