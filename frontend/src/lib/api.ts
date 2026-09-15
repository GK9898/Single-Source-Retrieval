import { UploadResponse, QueryResponse, EvaluateResponse, TopicItem } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

export async function queryDocument(
  query: string,
  documentId?: string,
  topK: number = 5,
  useReranker: boolean = true
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      document_id: documentId,
      top_k: topK,
      use_reranker: useReranker,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Query failed' }));
    throw new Error(error.detail || 'Query failed');
  }

  return response.json();
}

export async function fetchSuggestions(documentId?: string, numSuggestions: number = 3): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/suggestions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      num_suggestions: numSuggestions,
    }),
  });

  if (!response.ok) return [];
  const data = await response.json();
  return data.suggestions || [];
}

export async function fetchTopics(documentId?: string, maxTopics: number = 5): Promise<TopicItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/topics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      max_topics: maxTopics,
    }),
  });

  if (!response.ok) return [];
  const data = await response.json();
  return data.topics || [];
}

export async function fetchTTS(text: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) throw new Error('TTS synthesis failed');
  const data = await response.json();
  return data.audio_base64;
}

export async function evaluateQuery(
  query: string,
  answer: string,
  contexts: string[]
): Promise<EvaluateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      answer,
      contexts,
    }),
  });

  if (!response.ok) throw new Error('Evaluation failed');
  return response.json();
}
