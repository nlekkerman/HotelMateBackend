"""
Audio Transcription Service using OpenAI Whisper API
Converts audio files to text for command parsing
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def transcribe_audio(audio_file):
    """
    Transcribe audio file to text using OpenAI Whisper API
    
    Args:
        audio_file: Django UploadedFile object (webm, mp4, or ogg format)
        
    Returns:
        str: Transcribed text from audio
        
    Raises:
        Exception: If transcription fails or API error occurs
        
    Example:
        >>> transcribe_audio(request.FILES['audio'])
        "count guinness five point five"
    """
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Reset file pointer to beginning
        audio_file.seek(0)
        
        # OpenAI expects a tuple: (filename, file_object, content_type)
        # Create proper file tuple for the API
        file_tuple = (
            audio_file.name,
            audio_file.read(),
            audio_file.content_type
        )
        
        # Call Whisper API for transcription
        # Use prompt to hint at stocktake domain vocabulary
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=file_tuple,
            language="en",
            prompt="Stocktake voice commands: count, purchase, waste, product names, SKU codes, numbers"
        )
        
        # Extract transcribed text
        transcription = response.text.strip()
        
        logger.info(f"🎤 Transcribed: '{transcription}'")
        
        return transcription
        
    except ImportError:
        logger.error("OpenAI package not installed. Run: pip install openai")
        raise Exception("OpenAI package not installed")
        
    except AttributeError as e:
        logger.error(f"OpenAI API error (check API key or package version): {e}")
        raise Exception(f"OpenAI API configuration error: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Transcription failed: {str(e)}")
        raise Exception(f"Audio transcription failed: {str(e)}")
