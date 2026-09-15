from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models import UploadResponse
from app.services.document_processor import document_processor

router = APIRouter(prefix="/api", tags=["Document Ingestion"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF document, extract text, split into chunks, and build FAISS vector index."""
    if not file.filename.lower().endswith(".pdf") and not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF and TXT files are accepted."
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        result = document_processor.process_and_index(content, file.filename)
        return UploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )
