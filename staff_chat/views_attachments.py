"""
Views for Staff Chat File Attachments
Handles: upload, download, delete attachments
"""
import logging
import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from .models import (
    StaffConversation,
    StaffChatMessage,
    StaffChatAttachment
)
from .serializers_messages import StaffChatMessageSerializer
from .serializers_attachments import (
    StaffChatAttachmentSerializer,
    AttachmentUploadSerializer
)
from .permissions import IsStaffMember, IsSameHotel
from .pusher_utils import (
    broadcast_new_message,
    broadcast_attachment_uploaded,
    broadcast_attachment_deleted
)
from .fcm_utils import send_file_attachment_notification

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def upload_attachments(request, hotel_slug, conversation_id):
    """
    Upload file attachment(s) to a message
    POST /api/staff-chat/<hotel_slug>/conversations/<id>/upload/
    
    Supports:
    - Multiple files per request
    - Attach to existing message or create new message
    - Optional message text with files
    - Reply-to functionality
    
    Body (multipart/form-data):
    {
        "files": [File, File, ...],
        "message_id": <optional_existing_message_id>,
        "message": "Optional text",
        "reply_to": <optional_reply_to_message_id>
    }
    """
    conversation = get_object_or_404(
        StaffConversation,
        id=conversation_id,
        hotel__slug=hotel_slug
    )
    
    # Check if user is participant
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not conversation.participants.filter(id=staff.id).exists():
        return Response(
            {'error': 'You are not a participant in this conversation'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate upload data
    serializer = AttachmentUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    files = serializer.validated_data['files']
    message_id = serializer.validated_data.get('message_id')
    message_text = serializer.validated_data.get('message', '').strip()
    reply_to_id = serializer.validated_data.get('reply_to')
    
    # Get or create message
    if message_id:
        # Attach to existing message
        message = get_object_or_404(
            StaffChatMessage,
            id=message_id,
            conversation=conversation
        )
        
        # Verify sender
        if message.sender.id != staff.id:
            return Response(
                {'error': 'You can only attach files to your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(
            f"📎 Attaching {len(files)} file(s) to existing "
            f"message {message_id}"
        )
    else:
        # Create new message with attachments
        if not message_text:
            message_text = "[File shared]"
        
        # Get reply_to message if provided
        reply_to_message = None
        if reply_to_id:
            try:
                reply_to_message = StaffChatMessage.objects.get(
                    id=reply_to_id,
                    conversation=conversation
                )
            except StaffChatMessage.DoesNotExist:
                logger.warning(
                    f"Reply target message {reply_to_id} not found"
                )
        
        message = StaffChatMessage.objects.create(
            conversation=conversation,
            sender=staff,
            message=message_text,
            reply_to=reply_to_message
        )
        
        logger.info(
            f"📎 Created new message {message.id} with "
            f"{len(files)} file(s)"
        )
    
    # Process uploaded files
    attachments = []
    errors = []
    
    for file in files:
        try:
            # Create attachment
            attachment = StaffChatAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name,
                file_size=file.size,
                mime_type=file.content_type or ''
            )
            attachments.append(attachment)
            
            logger.info(
                f"✅ File uploaded: {file.name} "
                f"({file.size} bytes) by staff {staff.id}"
            )
        except Exception as e:
            errors.append(f"{file.name}: Upload failed - {str(e)}")
            logger.error(f"❌ Failed to upload {file.name}: {e}")
    
    if not attachments and errors:
        return Response(
            {'error': 'No valid files uploaded', 'details': errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Serialize attachments
    attachment_serializer = StaffChatAttachmentSerializer(
        attachments,
        many=True,
        context={'request': request}
    )
    
    # Get full message with attachments
    message_serializer = StaffChatMessageSerializer(
        message,
        context={'request': request}
    )
    
    message_data = json.loads(
        json.dumps(message_serializer.data, cls=DjangoJSONEncoder)
    )
    
    logger.info(
        f"📎 Uploaded {len(attachments)} file(s) to message "
        f"{message.id} by staff {staff.id}"
    )
    
    # Broadcast via Pusher
    if not message_id:
        # New message with files
        try:
            broadcast_new_message(
                hotel_slug,
                conversation.id,
                message_data
            )
            logger.info(
                f"✅ New message with attachments broadcasted"
            )
        except Exception as e:
            logger.error(f"❌ Failed to broadcast message: {e}")
    else:
        # Files added to existing message
        try:
            broadcast_attachment_uploaded(
                hotel_slug,
                conversation.id,
                {
                    'message_id': message.id,
                    'attachments': attachment_serializer.data
                }
            )
            logger.info(
                f"✅ Attachment upload broadcasted"
            )
        except Exception as e:
            logger.error(f"❌ Failed to broadcast attachment: {e}")
    
    # Send FCM notifications
    try:
        file_types = [att.file_type for att in attachments]
        
        for participant in conversation.participants.exclude(id=staff.id):
            send_file_attachment_notification(
                participant,
                staff,
                conversation,
                len(attachments),
                file_types
            )
        
        logger.info(
            f"📱 FCM notifications sent for file upload"
        )
    except Exception as e:
        logger.error(f"❌ Failed to send FCM notifications: {e}")
    
    response_data = {
        'message': message_data,
        'attachments': attachment_serializer.data,
        'success': True
    }
    
    if errors:
        response_data['warnings'] = errors
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def delete_attachment(request, hotel_slug, attachment_id):
    """
    Delete a file attachment
    DELETE /api/staff-chat/<hotel_slug>/attachments/<id>/delete/
    
    Only the message sender can delete attachments
    """
    attachment = get_object_or_404(
        StaffChatAttachment,
        id=attachment_id
    )
    
    message = attachment.message
    conversation = message.conversation
    
    # Verify hotel
    if conversation.hotel.slug != hotel_slug:
        return Response(
            {'error': 'Attachment does not belong to this hotel'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check permissions
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Only sender can delete their attachments
    if message.sender.id != staff.id:
        # Managers can delete any attachment
        if not (staff.role and staff.role.slug in ['manager', 'admin']):
            return Response(
                {'error': 'You can only delete your own attachments'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    logger.info(
        f"🗑️ Deleting attachment {attachment_id} from message "
        f"{message.id} by staff {staff.id}"
    )
    
    # Delete the file from storage
    if attachment.file:
        try:
            attachment.file.delete(save=False)
        except Exception as e:
            logger.warning(
                f"Failed to delete file from storage: {e}"
            )
    
    if attachment.thumbnail:
        try:
            attachment.thumbnail.delete(save=False)
        except Exception as e:
            logger.warning(
                f"Failed to delete thumbnail from storage: {e}"
            )
    
    attachment_id_copy = attachment.id
    attachment.delete()
    
    logger.info(
        f"✅ Attachment {attachment_id_copy} deleted"
    )
    
    # Broadcast deletion
    deletion_data = {
        'attachment_id': attachment_id_copy,
        'message_id': message.id,
        'deleted_by': staff.id,
        'timestamp': timezone.now().isoformat()
    }
    
    try:
        broadcast_attachment_deleted(
            hotel_slug,
            conversation.id,
            deletion_data
        )
        logger.info(
            f"✅ Attachment deletion broadcasted"
        )
    except Exception as e:
        logger.error(
            f"❌ Failed to broadcast attachment deletion: {e}"
        )
    
    return Response({
        'success': True,
        'attachment_id': attachment_id_copy,
        'message_id': message.id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def get_attachment_url(request, hotel_slug, attachment_id):
    """
    Get download URL for an attachment
    GET /api/staff-chat/<hotel_slug>/attachments/<id>/url/
    
    Returns temporary download URL (if using cloud storage)
    """
    attachment = get_object_or_404(
        StaffChatAttachment,
        id=attachment_id
    )
    
    conversation = attachment.message.conversation
    
    # Verify hotel
    if conversation.hotel.slug != hotel_slug:
        return Response(
            {'error': 'Attachment does not belong to this hotel'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user is participant
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not conversation.participants.filter(id=staff.id).exists():
        return Response(
            {'error': 'You are not a participant in this conversation'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get file URL
    file_url = None
    if attachment.file and hasattr(attachment.file, 'url'):
        file_url = attachment.file.url
        
        # For Cloudinary, URL is already absolute
        if not file_url.startswith(('http://', 'https://')):
            file_url = request.build_absolute_uri(file_url)
    
    thumbnail_url = None
    if attachment.thumbnail and hasattr(attachment.thumbnail, 'url'):
        thumbnail_url = attachment.thumbnail.url
        if not thumbnail_url.startswith(('http://', 'https://')):
            thumbnail_url = request.build_absolute_uri(thumbnail_url)
    
    return Response({
        'id': attachment.id,
        'file_name': attachment.file_name,
        'file_type': attachment.file_type,
        'file_size': attachment.file_size,
        'mime_type': attachment.mime_type,
        'file_url': file_url,
        'thumbnail_url': thumbnail_url,
        'uploaded_at': attachment.uploaded_at
    })
