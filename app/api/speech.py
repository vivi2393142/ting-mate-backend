import os

from fastapi import File, HTTPException, UploadFile

from app.core.api_decorator import post_route
from app.services.speech import speech_service

MAX_AUDIO_SIZE = 2 * 1024 * 1024  # 2MB


@post_route(
    path="/speech/transcribe",
    summary="Transcribe Audio",
    description="Transcribe audio file to text using AssemblyAI API.",
    tags=["speech"],
)
async def transcribe_audio(audio_file: UploadFile = File(...)):
    try:
        audio_content = await audio_file.read()
        if len(audio_content) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=400, detail="Audio file too large: max 2MB allowed."
            )
        ext = (
            os.path.splitext(audio_file.filename)[-1].replace(".", "").lower()
            if audio_file.filename
            else None
        )
        transcript = speech_service.transcribe_audio_content(
            audio_content, file_format=ext
        )
        if transcript:
            return {
                "success": True,
                "transcript": transcript,
                "message": "Audio transcribed successfully",
            }
        else:
            return {
                "success": False,
                "transcript": None,
                "message": "No speech detected in audio",
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}"
        )
