from fastapi import APIRouter, HTTPException, status
from app.models import QueryRequest, QueryResponse
from app.services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/api", tags=["RAG Query"])


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the indexed document store using full RAG retrieval & re-ranking pipeline."""
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        response = rag_pipeline.execute_query(
            query=request.query,
            document_id=request.document_id,
            top_k=request.top_k,
            use_reranker=request.use_reranker
        )
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )
