import logging
from typing import Optional

import assemblyai as aai

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """AssemblyAI Speech-to-Text service"""

    def __init__(self):
        aai.settings.api_key = settings.assemblyai_api_key

    def transcribe_audio_content(
        self, audio_content: bytes, file_format: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio content (bytes) using AssemblyAI.
        Args:
            audio_content: Audio file content as bytes
            file_format: Optional file extension (e.g., 'mp3', 'wav')
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Make a temporary file to store the audio content
            import tempfile

            suffix = f".{file_format}" if file_format else ""
            with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
                tmp.write(audio_content)
                tmp.flush()

                # Transcribe the audio content
                transcriber = aai.Transcriber()
                transcript = transcriber.transcribe(tmp.name)

                if transcript.status == "error":
                    logger.error(f"Transcription failed: {transcript.error}")
                    return None
                return transcript.text
        except Exception as e:
            logger.error(f"Error transcribing audio content: {str(e)}")
            return None


# Create global instance
speech_service = SpeechToTextService()
