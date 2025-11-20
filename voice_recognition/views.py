"""
Voice Command API View
Handles audio upload, transcription, and command parsing
Returns preview JSON only - does NOT modify database
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from hotel.models import Hotel
from stock_tracker.models import Stocktake
from .transcription import transcribe_audio
from .command_parser import parse_voice_command

logger = logging.getLogger(__name__)


class VoiceCommandView(APIView):
    """
    Handle voice command transcription and parsing for stocktake
    
    POST /api/stock_tracker/{hotel_identifier}/stocktake-lines/voice-command/
    
    Request:
        - Content-Type: multipart/form-data
        - audio (File): Audio blob (WebM/Opus, MP4, or OGG format)
        - stocktake_id (string): Stocktake context for validation
    
    Response (Success):
        {
            "success": true,
            "command": {
                "action": "count|purchase|waste",
                "item_identifier": "guinness",
                "value": 5.5,
                "full_units": 3,      // Optional
                "partial_units": 2.5,  // Optional
                "transcription": "count guinness five point five"
            },
            "stocktake_id": 123
        }
    
    Response (Error):
        {
            "success": false,
            "error": "Error message",
            "transcription": "..."  // Optional: included if transcription succeeded
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, hotel_identifier):
        """Process voice command and return parsed preview"""
        try:
            # 1. Validate request data
            audio_file = request.FILES.get('audio')
            stocktake_id = request.data.get('stocktake_id')
            
            if not audio_file:
                return Response({
                    'success': False,
                    'error': 'No audio file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not stocktake_id:
                return Response({
                    'success': False,
                    'error': 'No stocktake_id provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Validate audio file size (10MB max)
            max_size = 10 * 1024 * 1024  # 10MB
            if audio_file.size > max_size:
                return Response({
                    'success': False,
                    'error': f'Audio file too large (max {max_size/1024/1024}MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 3. Verify hotel and stocktake access
            hotel = get_object_or_404(
                Hotel,
                Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
            )
            
            stocktake = get_object_or_404(
                Stocktake,
                id=stocktake_id,
                hotel=hotel
            )
            
            # 4. Check stocktake not locked
            if stocktake.status == 'APPROVED':
                return Response({
                    'success': False,
                    'error': 'Stocktake is locked (approved)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(
                f"🎤 Voice command from {request.user.username} "
                f"| Hotel: {hotel_identifier} | Stocktake: {stocktake_id} "
                f"| Audio: {audio_file.size} bytes"
            )
            
            # 5. Transcribe audio to text
            try:
                transcription = transcribe_audio(audio_file)
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                return Response({
                    'success': False,
                    'error': f'Transcription failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 6. Parse command from transcription
            try:
                command = parse_voice_command(transcription)
            except ValueError as e:
                logger.warning(f"Parse failed: {e}")
                return Response({
                    'success': False,
                    'error': str(e),
                    'transcription': transcription
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 7. Return success response
            logger.info(f"✅ Voice command parsed successfully")
            
            return Response({
                'success': True,
                'command': command,
                'stocktake_id': int(stocktake_id)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
