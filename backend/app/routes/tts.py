import base64
from fastapi import APIRouter, HTTPException, status
from app.models import TTSRequest, TTSResponse

router = APIRouter(prefix="/api", tags=["Text to Speech"])


@router.post("/tts", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """Convert RAG response text into audio stream payload (Base64 MP3)."""
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text parameter cannot be empty."
        )

    try:
        # Dummy MP3 audio bytes payload for template demonstration
        # Real implementation integrates Google Cloud TTS or gTTS/elevenlabs
        dummy_audio_bytes = b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x00Lavf58.20.100\x00" * 20
        audio_b64 = base64.b64encode(dummy_audio_bytes).decode("utf-8")
        estimated_duration = round(len(request.text.split()) / 3.0, 1)

        return TTSResponse(
            audio_base64=audio_b64,
            format="mp3",
            duration_seconds=max(1.0, estimated_duration)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {str(e)}"
        )
