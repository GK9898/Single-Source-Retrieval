from fastapi import APIRouter, HTTPException, status
from app.models import EvaluateRequest, EvaluateResponse
from app.services.evaluator import rag_evaluator

router = APIRouter(prefix="/api", tags=["RAGAS Evaluation"])


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_rag(request: EvaluateRequest):
    """Evaluate query response fidelity, relevance, and recall using RAGAS metrics."""
    if not request.query.strip() or not request.answer.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query and Answer strings are required for evaluation."
        )

    try:
        res = rag_evaluator.evaluate_response(
            query=request.query,
            answer=request.answer,
            contexts=request.contexts,
            ground_truth=request.ground_truth
        )
        return EvaluateResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )
