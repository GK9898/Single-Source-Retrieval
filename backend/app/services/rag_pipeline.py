import time
import logging
import json
import re
from typing import List, Dict, Any, Tuple
import httpx
from app.config import settings
from app.services.document_processor import document_processor
from app.services.reranker import reranker_service
from app.utils.retry import llm_retry_decorator

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        pass

    def classify_and_decompose(self, query: str) -> Tuple[str, List[str]]:
        """Classify query type (single_fact, multi_part, summarization) and decompose multi-part queries into sub-questions."""
        q_lower = query.lower().strip()

        # 1. Summarization check
        if any(term in q_lower for term in ["summarize", "summary", "overview", "main points", "key topics"]):
            return "summarization", [query]

        # 2. Multi-part / Comparison check heuristic
        is_multi_part = False
        if "?" in query and query.count("?") > 1:
            is_multi_part = True
        elif any(connector in q_lower for connector in [" and how ", " and what ", " and why ", " compare ", " vs ", " as well as "]):
            is_multi_part = True
        elif ";" in query or " & " in query:
            is_multi_part = True

        if not is_multi_part:
            return "single_fact", [query]

        # Try LLM decomposition if API key available
        if settings.OPENROUTER_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a query decomposition assistant. Decompose multi-part user questions "
                                "into a JSON array of 2-3 distinct, standalone sub-queries. "
                                "Respond ONLY with a valid JSON array of strings, e.g. [\"subquery 1\", \"subquery 2\"]."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Decompose this query: {query}"
                        }
                    ]
                }
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        content = response.json()["choices"][0]["message"]["content"]
                        match = re.search(r"\[.*\]", content, re.DOTALL)
                        if match:
                            sub_qs = json.loads(match.group(0))
                            if isinstance(sub_qs, list) and len(sub_qs) > 0:
                                return "multi_part", sub_qs
            except Exception as e:
                logger.warning(f"LLM query decomposition failed ({e}). Using rule-based decomposer.")

        # Fallback Rule-Based Decomposition
        sub_queries = []
        raw_parts = re.split(r"\?|;|\band\b|\bvs\b|\bcompare\b", query, flags=re.IGNORECASE)
        for part in raw_parts:
            cleaned = part.strip()
            if len(cleaned) > 5:
                sub_queries.append(cleaned)

        if len(sub_queries) <= 1:
            sub_queries = [query]

        return "multi_part", sub_queries

    @llm_retry_decorator(max_attempts=2)
    def _generate_answer(self, query: str, context_texts: List[str]) -> str:
        """Synthesize answer using retrieved context via OpenRouter API (or fallback generator)."""
        if not context_texts:
            return "This information is not present in the document."

        joined_context = "\n---\n".join(context_texts)

        # Stop words filter for accurate out-of-scope query detection
        STOP_WORDS = {"what", "is", "the", "current", "of", "for", "how", "to", "are", "in", "and", "or", "a", "an", "this", "that", "with", "by", "at", "from", "which", "where", "when", "who", "do", "does", "did"}
        q_content_words = set(re.findall(r"\b\w+\b", query.lower())) - STOP_WORDS
        q_content_words = {w for w in q_content_words if len(w) > 2}

        combined_text_words = set(re.findall(r"\b\w+\b", joined_context.lower()))

        # Check content word overlap: if 0 content words match, return out-of-scope rejection
        matched_content_words = q_content_words.intersection(combined_text_words)
        if len(q_content_words) > 0 and len(matched_content_words) == 0:
            return "This information is not present in the document."

        if settings.OPENROUTER_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a strict, document-grounded question-answering assistant.\n"
                                "Rules:\n"
                                "1. Answer the user's question using ONLY the provided document context.\n"
                                "2. Do NOT use outside knowledge or hallucinate facts not stated in the context.\n"
                                "3. If the answer cannot be found in the provided document context, explicitly state: 'This information is not present in the document.'"
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Document Context:\n{joined_context}\n\nUser Question: {query}"
                        }
                    ]
                }
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        logger.warning(f"OpenRouter API call returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error making OpenRouter API call: {e}")

        # Dynamic fallback answer generation (extracts keyword-matching sentences per query)
        relevant_snippets = []

        for text in context_texts:
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 10]
            for s in sentences:
                s_words = set(re.findall(r"\b\w+\b", s.lower()))
                if q_content_words.intersection(s_words):
                    relevant_snippets.append(s)

        if not relevant_snippets:
            return "This information is not present in the document."

        # Pick top 3 unique matching sentences
        unique_snippets = list(dict.fromkeys(relevant_snippets))[:3]
        bullet_points = "\n".join([f"- {snip}." if not snip.endswith(".") else f"- {snip}" for snip in unique_snippets])

        answer = (
            f"Based on the retrieved document context for '{query}':\n\n"
            f"{bullet_points}\n\n"
            f"(Note: To enable generative LLM answers, add your OPENROUTER_API_KEY in backend/.env)"
        )
        return answer




    def execute_query(
        self, query: str, document_id: str = None, top_k: int = 5, use_reranker: bool = True
    ) -> Dict[str, Any]:
        """Execute full RAG retrieval, query decomposition, optional re-ranking, and response synthesis."""
        start_time = time.time()

        # Step 1: Query Routing & Decomposition (Step 6 requirement)
        query_type, sub_queries = self.classify_and_decompose(query)
        logger.info(f"Query routing classified query as '{query_type}' with sub_queries: {sub_queries}")

        # Step 2: Vector retrieval per sub-query or main query
        candidate_chunks_map: Dict[str, Dict[str, Any]] = {}
        fetch_k = top_k * 2 if use_reranker else top_k

        if query_type == "multi_part" and len(sub_queries) > 1:
            for sub_q in sub_queries:
                sub_results = document_processor.search_similar_chunks(
                    query=sub_q, doc_id=document_id, top_k=fetch_k
                )
                for chunk in sub_results:
                    cid = chunk["chunk_id"]
                    if cid not in candidate_chunks_map or chunk.get("score", 0.0) > candidate_chunks_map[cid].get("score", 0.0):
                        candidate_chunks_map[cid] = chunk
            initial_chunks = list(candidate_chunks_map.values())
        else:
            initial_chunks = document_processor.search_similar_chunks(
                query=query, doc_id=document_id, top_k=fetch_k
            )

        # Step 3: Cross-encoder Re-ranking if enabled (Step 7 requirement)
        if use_reranker and initial_chunks:
            logger.info(f"=== PRE-RERANK FAISS ORDERING for '{query}' ===")
            for rank, c in enumerate(initial_chunks[:5], start=1):
                logger.info(f"  Pre-Rank #{rank}: Chunk {c['chunk_id']} (Page {c.get('page_number')}) | Vector Score: {c.get('score', 0.0):.4f}")

            reranked_chunks = reranker_service.rerank(query=query, chunks=initial_chunks, top_k=top_k)

            logger.info(f"=== POST-RERANK CROSS-ENCODER ORDERING for '{query}' ===")
            for rank, c in enumerate(reranked_chunks[:5], start=1):
                logger.info(f"  Post-Rank #{rank}: Chunk {c['chunk_id']} (Page {c.get('page_number')}) | Re-rank Score: {c.get('score', 0.0):.4f}")
        else:
            reranked_chunks = initial_chunks[:top_k]


        # Step 4: Adjacent Chunk Context Stitching (prevents truncated multi-step procedures)
        final_chunks = document_processor.get_expanded_chunks_context(doc_id=document_id, retrieved_chunks=reranked_chunks)

        # Step 5: LLM Generation
        context_texts = [c["text"] for c in final_chunks]
        answer = self._generate_answer(query, context_texts)


        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    "score": round(float(c.get("score", 0.0)), 4),
                    "page_number": c.get("page_number"),
                    "metadata": c.get("metadata", {})
                }
                for c in final_chunks
            ],
            "execution_time_ms": execution_time_ms,
            "document_id": document_id,
            "query_type": query_type,
            "sub_queries": sub_queries
        }


rag_pipeline = RAGPipeline()

