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
from stock_tracker.models import Stocktake, StocktakeLine, StockItem
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


class VoiceCommandConfirmView(APIView):
    """
    Confirm and apply a voice command to update stocktake line
    
    POST /api/stock_tracker/{hotel_identifier}/stocktake-lines/voice-command/confirm/
    
    Request:
        {
            "stocktake_id": 123,
            "command": {
                "action": "count|purchase|waste",
                "item_identifier": "guinness",
                "value": 5.5,
                "full_units": 3,      // Optional
                "partial_units": 2.5  // Optional
            }
        }
    
    Response (Success):
        {
            "success": true,
            "line": {...},  // Updated StocktakeLine data
            "message": "Counted 5.5 units of Guinness"
        }
    
    Response (Error):
        {
            "success": false,
            "error": "Error message"
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, hotel_identifier):
        """Apply confirmed voice command to stocktake line"""
        try:
            stocktake_id = request.data.get('stocktake_id')
            command = request.data.get('command')
            
            if not stocktake_id or not command:
                return Response({
                    'success': False,
                    'error': 'Missing stocktake_id or command'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate hotel and stocktake
            hotel = get_object_or_404(
                Hotel,
                Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
            )
            
            stocktake = get_object_or_404(
                Stocktake,
                id=stocktake_id,
                hotel=hotel
            )
            
            if stocktake.status == 'APPROVED':
                return Response({
                    'success': False,
                    'error': 'Stocktake is locked (approved)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the stock item using fuzzy matching
            item_identifier = command.get('item_identifier', '').strip()
            
            # Use fuzzy matching to find best item match
            from .item_matcher import find_best_match_in_stocktake
            
            match_result = find_best_match_in_stocktake(
                item_identifier,
                stocktake,
                min_score=0.55
            )
            
            if not match_result:
                # Fallback: try exact/contains match in all hotel items
                stock_item = StockItem.objects.filter(
                    hotel=hotel,
                    active=True
                ).filter(
                    Q(sku__iexact=item_identifier) |
                    Q(name__iexact=item_identifier) |
                    Q(sku__icontains=item_identifier) |
                    Q(name__icontains=item_identifier)
                ).first()
            else:
                stock_item = match_result['item']
            
            if not stock_item:
                return Response({
                    'success': False,
                    'error': f'Stock item not found: {item_identifier}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get or create stocktake line
            line, created = StocktakeLine.objects.get_or_create(
                stocktake=stocktake,
                item=stock_item,
                defaults={
                    'opening_qty': stock_item.total_stock_in_servings or 0,
                    'valuation_cost': stock_item.current_cost or 0,
                }
            )
            
            # Apply the command based on action
            action = command.get('action')
            value = command.get('value', 0)
            full_units = command.get('full_units')
            partial_units = command.get('partial_units')
            
            if action == 'count':
                # Update counted values
                if full_units is not None and partial_units is not None:
                    line.counted_full_units = full_units
                    line.counted_partial_units = partial_units
                else:
                    # Single value - put it in full_units
                    line.counted_full_units = value
                    line.counted_partial_units = 0
                
                line.save()
                message = f"Counted {value} units of {stock_item.name}"
                
            elif action == 'purchase':
                # Add to purchases
                from decimal import Decimal
                line.purchases += Decimal(str(value))
                line.save()
                message = f"Added purchase of {value} units of {stock_item.name}"
                
            elif action == 'waste':
                # Add to waste
                from decimal import Decimal
                line.waste += Decimal(str(value))
                line.save()
                message = f"Added waste of {value} units of {stock_item.name}"
                
            else:
                return Response({
                    'success': False,
                    'error': f'Unknown action: {action}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(
                f"✅ Applied voice command: {action} {stock_item.sku} = {value}"
            )
            
            # Return updated line data
            from stock_tracker.serializers import StocktakeLineSerializer
            serializer = StocktakeLineSerializer(line)
            
            return Response({
                'success': True,
                'line': serializer.data,
                'message': message,
                'item_name': stock_item.name,
                'item_sku': stock_item.sku
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Confirm failed: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to apply command',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
