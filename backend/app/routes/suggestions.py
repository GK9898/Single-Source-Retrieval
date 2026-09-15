from fastapi import APIRouter
from app.models import SuggestionsRequest, SuggestionsResponse
from app.services.document_processor import document_processor

router = APIRouter(prefix="/api", tags=["Prompt Suggestions"])


@router.post("/suggestions", response_model=SuggestionsResponse)
async def generate_suggestions(request: SuggestionsRequest):
    """Generate contextual follow-up question suggestions based on document content."""
    doc_id = request.document_id
    if not doc_id and document_processor.documents_store:
        doc_id = list(document_processor.documents_store.keys())[-1]

    doc_data = document_processor.documents_store.get(doc_id) if doc_id else None

    if doc_data and doc_data.get("chunks"):
        first_chunk = doc_data["chunks"][0]["text"]
        words = [w.strip(",.!?") for w in first_chunk.split() if len(w) > 4][:5]
        keyword = words[0] if words else "document"

        suggestions = [
            f"What are the main key points regarding {keyword} in this document?",
            f"Can you summarize section 1 of {doc_data['filename']}?",
            f"What conclusions or metrics are highlighted for {keyword}?",
            "What critical methodology or background is discussed?"
        ]
    else:
        suggestions = [
            "What are the primary objectives of this document?",
            "Can you provide a high-level summary of the main sections?",
            "What key data or statistical metrics are reported?"
        ]

    return SuggestionsResponse(suggestions=suggestions[:request.num_suggestions])
