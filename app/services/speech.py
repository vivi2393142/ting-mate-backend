import logging
from typing import Optional

from google.cloud import speech
from google.cloud.speech import RecognitionAudio, RecognitionConfig

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """Google Speech-to-Text service"""

    def __init__(self):
        # Only initialize Google Cloud services if not in test environment
        if settings.environment != "test":
            self.client = speech.SpeechClient()
            self.config = RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=settings.speech_to_text_sample_rate_hertz,
                language_code=settings.speech_to_text_language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                enable_word_confidence=True,
            )
        else:
            # In test environment, set client to None
            self.client = None
            self.config = None
            logger.info(
                "Speech service initialized in test mode - Google Cloud services disabled"
            )

    async def transcribe_audio(
        self, audio_content: bytes, encoding: str = "LINEAR16"
    ) -> Optional[str]:
        """
        Convert audio file to text

        Args:
            audio_content: Audio content (bytes)
            encoding: Audio encoding format

        Returns:
            Converted text, or None if failed
        """
        try:
            # In test environment, return mock transcript
            if settings.environment == "test":
                logger.info("Test mode: Mock speech-to-text response")
                return "This is a test transcript from test mode"

            # Set audio encoding
            if encoding.upper() == "MP3":
                config = RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                    sample_rate_hertz=settings.speech_to_text_sample_rate_hertz,
                    language_code=settings.speech_to_text_language_code,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=False,
                    enable_word_confidence=True,
                )
            elif encoding.upper() == "M4A":
                config = RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # M4A uses MP3 encoding
                    sample_rate_hertz=settings.speech_to_text_sample_rate_hertz,
                    language_code=settings.speech_to_text_language_code,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=False,
                    enable_word_confidence=True,
                )
            else:
                config = self.config

            # Create audio object
            audio = RecognitionAudio(content=audio_content)

            # Call Speech-to-Text API
            response = self.client.recognize(config=config, audio=audio)

            # Process response
            if not response.results:
                logger.warning("Speech-to-Text API returned no results")
                return None

            # Merge all transcription results
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript + " "

            logger.info(f"Speech to text successful: {transcript.strip()}")
            return transcript.strip()

        except Exception as e:
            logger.error(f"Speech to text failed: {str(e)}")
            return None

    def validate_audio_file(self, audio_content: bytes, max_size_mb: int = 10) -> bool:
        """
        Validate audio file format and size

        Args:
            audio_content: Audio content
            max_size_mb: Maximum file size (MB)

        Returns:
            Whether the audio file is valid
        """
        # Check file size
        size_mb = len(audio_content) / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(f"Audio file too large: {size_mb:.2f}MB > {max_size_mb}MB")
            return False

        # Check file format (simple header check)
        if len(audio_content) < 4:
            return False

        # Check common audio format headers
        file_header = audio_content[:4]

        # WAV: RIFF
        if file_header.startswith(b"RIFF"):
            return True

        # MP3: ID3 or MPEG
        if (
            file_header.startswith(b"ID3")
            or file_header.startswith(b"\xff\xfb")
            or file_header.startswith(b"\xff\xf3")
        ):
            return True

        # M4A: ftyp
        if file_header.startswith(b"ftyp"):
            return True

        logger.warning("Unsupported audio format")
        return False


# Create global instance
speech_service = SpeechToTextService()
