"""
Views for Staff Chat Message Operations
Handles: send, edit, delete, reply, reactions
"""
import logging
import json
import re
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
    StaffMessageReaction
)
from .serializers_messages import (
    StaffChatMessageSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
    MessageReactionCreateSerializer,
    MessageReactionSerializer,
    ForwardMessageSerializer
)
from .permissions import (
    IsStaffMember,
    IsConversationParticipant,
    IsMessageSender,
    IsSameHotel,
    CanDeleteMessage
)
from notifications.notification_manager import notification_manager
from .fcm_utils import notify_conversation_participants
from staff.models import Staff

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def mark_message_as_read(request, hotel_slug, message_id):
    """
    Mark a specific message as read by current user
    POST /api/staff-chat/<hotel_slug>/messages/<id>/mark-as-read/
    
    Useful for marking individual messages in group chats
    Returns updated message with read status
    """
    from .pusher_utils import broadcast_read_receipt
    
    message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check if user is participant
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not message.conversation.participants.filter(id=staff.id).exists():
        return Response(
            {'error': 'You are not a participant in this conversation'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark as read
    was_unread = not message.read_by.filter(id=staff.id).exists()
    
    if was_unread and staff.id != message.sender.id:
        message.mark_as_read_by(staff)
        
        # Broadcast read receipt
        try:
            staff_name = f"{staff.first_name} {staff.last_name}".strip()
            broadcast_read_receipt(
                hotel_slug,
                message.conversation.id,
                {
                    'staff_id': staff.id,
                    'staff_name': staff_name,
                    'message_ids': [message.id],
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(
                f"✅ Read receipt broadcasted for message {message.id}"
            )
        except Exception:
            # Log but don't fail the request
            logger.warning(
                f"Failed to broadcast read receipt for message {message.id}"
            )
    
    # Serialize and return updated message
    serializer = StaffChatMessageSerializer(
        message,
        context={'request': request}
    )
    
    return Response({
        'success': True,
        'was_unread': was_unread,
        'message': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def send_message(request, hotel_slug, conversation_id):
    """
    Send a new message in a conversation
    POST /api/staff-chat/<hotel_slug>/conversations/<id>/send-message/
    
    Body:
    {
        "message": "Hello!",
        "reply_to": <message_id>  // optional
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
    
    # Validate and create message
    serializer = MessageCreateSerializer(data={
        'conversation': conversation.id,
        'message': request.data.get('message', '').strip(),
        'reply_to': request.data.get('reply_to')
    })
    
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    message_text = serializer.validated_data['message']
    reply_to_id = serializer.validated_data.get('reply_to')
    
    # Get reply_to message if provided
    reply_to_message = None
    if reply_to_id:
        try:
            reply_to_message = StaffChatMessage.objects.get(
                id=reply_to_id,
                conversation=conversation
            )
            logger.info(
                f"Message replying to message ID: {reply_to_id}"
            )
        except StaffChatMessage.DoesNotExist:
            logger.warning(
                f"Reply target message {reply_to_id} not found"
            )
    
    # Extract @mentions from message
    mention_pattern = r'@(\w+(?:\s+\w+)?)'
    mentioned_names = re.findall(mention_pattern, message_text)
    mentioned_staff = []
    
    if mentioned_names:
        for name in mentioned_names:
            # Try to find staff by name
            name_parts = name.strip().split()
            if len(name_parts) == 1:
                # Single name - search first or last name
                mentioned = Staff.objects.filter(
                    hotel=conversation.hotel,
                    first_name__icontains=name_parts[0]
                ).first() or Staff.objects.filter(
                    hotel=conversation.hotel,
                    last_name__icontains=name_parts[0]
                ).first()
            else:
                # Full name
                mentioned = Staff.objects.filter(
                    hotel=conversation.hotel,
                    first_name__icontains=name_parts[0],
                    last_name__icontains=name_parts[1]
                ).first()
            
            if mentioned and mentioned not in mentioned_staff:
                mentioned_staff.append(mentioned)
    
    logger.info(
        f"🔵 NEW STAFF MESSAGE | Sender: {staff} | "
        f"Conversation: {conversation.id} | "
        f"Hotel: {hotel_slug} | "
        f"Reply to: {reply_to_id if reply_to_id else 'None'} | "
        f"Mentions: {len(mentioned_staff)}"
    )
    
    # Create the message
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=staff,
        message=message_text,
        reply_to=reply_to_message
    )
    
    # Add mentions
    if mentioned_staff:
        message.mentions.set(mentioned_staff)
    
    # Update conversation
    conversation.has_unread = True
    conversation.save()
    
    logger.info(
        f"📝 Message created | ID: {message.id} | "
        f"Mentions: {[s.id for s in mentioned_staff]}"
    )
    
    # Serialize message
    message_serializer = StaffChatMessageSerializer(
        message,
        context={'request': request}
    )
    
    # Convert to JSON-safe format
    message_data = json.loads(
        json.dumps(message_serializer.data, cls=DjangoJSONEncoder)
    )
    
    # Remove sender-specific field before broadcasting
    # Recipients will calculate this themselves based on their own ID
    if 'is_read_by_current_user' in message_data:
        del message_data['is_read_by_current_user']
    
    # Broadcast via NotificationManager to all participants
    try:
        notification_manager.realtime_staff_chat_message_created(message)
        logger.info(
            f"✅ Realtime broadcast successful for message {message.id}"
        )
        
        # 🔥 UPDATE UNREAD COUNT for recipients (excluding sender)
        for recipient in conversation.participants.exclude(id=staff.id):
            notification_manager.realtime_staff_chat_unread_updated(
                staff=recipient,
                conversation=conversation
            )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to broadcast message via Pusher: {e}"
        )
    
    # Send FCM notifications to participants (except sender)
    try:
        mentioned_ids = [s.id for s in mentioned_staff]
        success, total = notify_conversation_participants(
            conversation,
            staff,
            message_text,
            exclude_sender=True,
            mentions=mentioned_ids
        )
        logger.info(
            f"📱 FCM notifications sent: {success}/{total}"
        )
    except Exception as e:
        logger.error(
            f"❌ Failed to send FCM notifications: {e}"
        )
    
    logger.info(
        f"✅ MESSAGE COMPLETE | ID: {message.id} | "
        f"Sender: {staff} | Conversation: {conversation.id}"
    )
    
    return Response(message_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def get_conversation_messages(request, hotel_slug, conversation_id):
    """
    Get messages for a conversation with pagination
    GET /api/staff-chat/<hotel_slug>/conversations/<id>/messages/
    
    Query params:
    - limit: Number of messages to load (default: 50)
    - before_id: Load messages older than this ID
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
    
    # Pagination parameters
    limit = int(request.GET.get('limit', 50))
    before_id = request.GET.get('before_id')
    
    # Query messages
    messages_qs = conversation.messages.filter(
        is_deleted=False
    ).select_related('sender').prefetch_related(
        'attachments',
        'reactions',
        'read_by',
        'mentions'
    ).order_by('-timestamp')
    
    if before_id:
        messages_qs = messages_qs.filter(id__lt=before_id)
    
    messages = messages_qs[:limit]
    
    # Reverse to show oldest first
    messages = list(messages)[::-1]
    
    serializer = StaffChatMessageSerializer(
        messages,
        many=True,
        context={'request': request}
    )
    
    return Response({
        'messages': serializer.data,
        'count': len(messages),
        'has_more': messages_qs.count() > limit
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def edit_message(request, hotel_slug, message_id):
    """
    Edit/update a message
    PATCH /api/staff-chat/<hotel_slug>/messages/<id>/edit/
    
    Body:
    {
        "message": "Updated text"
    }
    """
    message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check permissions
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Only sender can edit their own messages
    if message.sender.id != staff.id:
        return Response(
            {'error': 'You can only edit your own messages'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Cannot edit deleted messages
    if message.is_deleted:
        return Response(
            {'error': 'Cannot edit a deleted message'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate and update
    serializer = MessageUpdateSerializer(
        message,
        data=request.data,
        partial=True
    )
    
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer.save()
    
    logger.info(
        f"✏️ Message {message_id} edited by staff {staff.id}"
    )
    
    # Broadcast update via Pusher
    message_serializer = StaffChatMessageSerializer(
        message,
        context={'request': request}
    )
    
    message_data = json.loads(
        json.dumps(message_serializer.data, cls=DjangoJSONEncoder)
    )
    
    # Remove sender-specific field before broadcasting
    if 'is_read_by_current_user' in message_data:
        del message_data['is_read_by_current_user']
    
    try:
        notification_manager.realtime_staff_chat_message_edited(message)
        logger.info(
            f"✅ Message edit broadcasted via realtime"
        )
    except Exception as e:
        logger.error(
            f"❌ Failed to broadcast message edit: {e}"
        )
    
    return Response(message_data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def delete_message(request, hotel_slug, message_id):
    """
    Delete a message (soft or hard delete)
    DELETE /api/staff-chat/<hotel_slug>/messages/<id>/delete/
    
    Query params:
    - hard_delete: true for permanent deletion (managers only)
    """
    message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check permissions
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    conversation = message.conversation
    hard_delete = request.query_params.get('hard_delete') == 'true'
    
    # Permission check for deletion
    if message.sender.id != staff.id:
        # Only managers can delete others' messages
        if not (staff.role and staff.role.slug in ['manager', 'admin']):
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Hard delete permission check
    if hard_delete:
        if message.sender.id != staff.id:
            if not (staff.role and staff.role.slug in ['manager', 'admin']):
                return Response(
                    {
                        'error': 'Only managers can permanently '
                                 'delete messages'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
    
    logger.info(
        f"🗑️ DELETE REQUEST | Message: {message_id} | "
        f"Staff: {staff.id} | Hard: {hard_delete} | "
        f"Hotel: {hotel_slug}"
    )
    
    if hard_delete:
        # Hard delete - permanently remove
        message_id_copy = message.id
        conversation_id = conversation.id
        
        # Get attachment IDs before deleting
        attachment_ids = list(
            message.attachments.values_list('id', flat=True)
        )
        
        deletion_data = {
            "message_id": message_id_copy,
            "hard_delete": True,
            "attachment_ids": attachment_ids,
            "deleted_by": staff.id,
            "timestamp": timezone.now().isoformat()
        }
        
        message.delete()
        
        logger.info(
            f"🗑️ Message {message_id_copy} hard deleted by "
            f"staff {staff.id}"
        )
        
        # Broadcast deletion
        try:
            notification_manager.realtime_staff_chat_message_deleted(
                message_id_copy, 
                conversation_id, 
                conversation.hotel
            )
            logger.info(
                f"✅ Hard deletion broadcasted via realtime"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to broadcast hard deletion: {e}"
            )
        
        return Response({
            'success': True,
            'hard_delete': True,
            'message_id': message_id_copy
        })
    
    else:
        # Soft delete - mark as deleted
        message.soft_delete()
        
        logger.info(
            f"🗑️ Message {message_id} soft deleted by staff {staff.id}"
        )
        
        # Serialize updated message
        message_serializer = StaffChatMessageSerializer(
            message,
            context={'request': request}
        )
        
        message_data = json.loads(
            json.dumps(message_serializer.data, cls=DjangoJSONEncoder)
        )
        
        deletion_data = {
            "message_id": message.id,
            "hard_delete": False,
            "message": message_data,
            "deleted_by": staff.id,
            "timestamp": timezone.now().isoformat()
        }
        
        # Broadcast deletion
        try:
            notification_manager.realtime_staff_chat_message_deleted(
                message.id, 
                conversation.id, 
                conversation.hotel
            )
            logger.info(
                f"✅ Soft deletion broadcasted via realtime"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to broadcast soft deletion: {e}"
            )
        
        return Response({
            'success': True,
            'hard_delete': False,
            'message': message_data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def add_reaction(request, hotel_slug, message_id):
    """
    Add an emoji reaction to a message
    POST /api/staff-chat/<hotel_slug>/messages/<id>/react/
    
    Body:
    {
        "emoji": "👍"
    }
    """
    message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check if user is participant
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not message.conversation.participants.filter(id=staff.id).exists():
        return Response(
            {'error': 'You are not a participant in this conversation'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate emoji
    serializer = MessageReactionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    emoji = serializer.validated_data['emoji']
    
    # Remove any existing reactions by this user on this message
    existing_reactions = StaffMessageReaction.objects.filter(
        message=message,
        staff=staff
    )
    
    removed_reactions = []
    if existing_reactions.exists():
        # Store reaction info before deletion for broadcast
        for old_reaction in existing_reactions:
            removed_reactions.append({
                'id': old_reaction.id,
                'emoji': old_reaction.emoji,
                'staff': staff.id
            })
        existing_reactions.delete()
        logger.info(
            f"🔄 Removed {len(removed_reactions)} existing reaction(s) "
            f"by staff {staff.id} on message {message_id}"
        )
    
    # Create the new reaction
    reaction = StaffMessageReaction.objects.create(
        message=message,
        staff=staff,
        emoji=emoji
    )
    
    logger.info(
        f"👍 Reaction added: {emoji} by staff {staff.id} "
        f"on message {message_id}"
    )
    
    # Serialize reaction
    reaction_serializer = MessageReactionSerializer(reaction)
    
    # Broadcast removed reactions (if any) and new reaction via Pusher
    try:
        # First, broadcast removal of old reactions
        for removed in removed_reactions:
            removal_data = {
                'message_id': message.id,
                'reaction': removed,
                'action': 'remove'
            }
            # TODO: Implement realtime_staff_chat_message_reaction_removed in NotificationManager
            # broadcast_message_reaction(
            #     hotel_slug,
            #     message.conversation.id,
            #     removal_data
            # )
        
        # Then broadcast the new reaction
        reaction_data = {
            'message_id': message.id,
            'reaction': reaction_serializer.data,
            'action': 'add'
        }
        # TODO: Implement realtime_staff_chat_message_reaction_added in NotificationManager
        # broadcast_message_reaction(
        #     hotel_slug,
        #     message.conversation.id,
        #     reaction_data
        # )
        logger.info(
            f"✅ Reaction change broadcasted via Pusher "
            f"(removed: {len(removed_reactions)}, added: 1)"
        )
    except Exception as e:
        logger.error(
            f"❌ Failed to broadcast reaction: {e}"
        )
    
    return Response(
        reaction_serializer.data,
        status=status.HTTP_201_CREATED
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def remove_reaction(request, hotel_slug, message_id, emoji):
    """
    Remove an emoji reaction from a message
    DELETE /api/staff-chat/<hotel_slug>/messages/<id>/react/<emoji>/
    """
    message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check if user is participant
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find and delete reaction
    try:
        reaction = StaffMessageReaction.objects.get(
            message=message,
            staff=staff,
            emoji=emoji
        )
        reaction_id = reaction.id
        reaction.delete()
        
        logger.info(
            f"❌ Reaction removed: {emoji} by staff {staff.id} "
            f"on message {message_id}"
        )
        
        # Broadcast reaction removal
        reaction_data = {
            'message_id': message.id,
            'reaction': {
                'id': reaction_id,
                'emoji': emoji,
                'staff': staff.id
            },
            'action': 'remove'
        }
        
        try:
            # TODO: Implement realtime_staff_chat_message_reaction_removed in NotificationManager
            # broadcast_message_reaction(
            #     hotel_slug,
            #     message.conversation.id,
            #     reaction_data
            # )
            logger.info(
                f"✅ Reaction removal would be broadcasted (currently disabled)"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to broadcast reaction removal: {e}"
            )
        
        return Response(
            {'message': 'Reaction removed'},
            status=status.HTTP_200_OK
        )
        
    except StaffMessageReaction.DoesNotExist:
        return Response(
            {'error': 'Reaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def forward_message(request, hotel_slug, message_id):
    """
    Forward a message to multiple conversations
    POST /api/staff-chat/<hotel_slug>/messages/<id>/forward/
    
    Body:
    {
        "conversation_ids": [1, 2, 3],  // existing conversations
        "new_participant_ids": [4, 5]   // create new conversations
    }
    
    Returns:
    {
        "success": true,
        "forwarded_to_existing": 3,
        "forwarded_to_new": 2,
        "total_forwarded": 5,
        "results": [
            {
                "conversation_id": 1,
                "message_id": 123,
                "created_conversation": false
            },
            ...
        ]
    }
    """
    # Get the original message
    original_message = get_object_or_404(
        StaffChatMessage,
        id=message_id,
        conversation__hotel__slug=hotel_slug
    )
    
    # Check if user has access
    try:
        staff = request.user.staff_profile
    except AttributeError:
        return Response(
            {'error': 'Staff profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify staff is participant in original conversation
    if not original_message.conversation.participants.filter(
        id=staff.id
    ).exists():
        return Response(
            {
                'error': 'You must be a participant in the conversation '
                         'to forward messages'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Cannot forward deleted messages
    if original_message.is_deleted:
        return Response(
            {'error': 'Cannot forward a deleted message'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate request data
    serializer = ForwardMessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    conversation_ids = serializer.validated_data.get('conversation_ids', [])
    new_participant_ids = serializer.validated_data.get(
        'new_participant_ids',
        []
    )
    
    hotel = original_message.conversation.hotel
    results = []
    forwarded_to_existing = 0
    forwarded_to_new = 0
    
    logger.info(
        f"📤 FORWARD MESSAGE | Message: {message_id} | "
        f"From Staff: {staff.id} | "
        f"To Conversations: {conversation_ids} | "
        f"New Participants: {new_participant_ids} | "
        f"Hotel: {hotel_slug}"
    )
    
    # Forward to existing conversations
    for conv_id in conversation_ids:
        try:
            conversation = StaffConversation.objects.get(
                id=conv_id,
                hotel=hotel
            )
            
            # Verify user is participant in target conversation
            if not conversation.participants.filter(id=staff.id).exists():
                results.append({
                    'conversation_id': conv_id,
                    'error': 'You are not a participant in this conversation',
                    'created_conversation': False,
                    'success': False
                })
                continue
            
            # Create forwarded message
            forwarded_msg = StaffChatMessage.objects.create(
                conversation=conversation,
                sender=staff,
                message=original_message.message,
                reply_to=None  # Forwarded messages don't preserve reply chain
            )
            
            # Update conversation timestamp
            conversation.has_unread = True
            conversation.save()
            
            # Broadcast the forwarded message
            message_serializer = StaffChatMessageSerializer(
                forwarded_msg,
                context={'request': request}
            )
            message_data = json.loads(
                json.dumps(
                    message_serializer.data,
                    cls=DjangoJSONEncoder
                )
            )
            
            # Remove sender-specific field before broadcasting
            if 'is_read_by_current_user' in message_data:
                del message_data['is_read_by_current_user']
            
            try:
                notification_manager.realtime_staff_chat_message_created(forwarded_msg)
            except Exception as e:
                logger.error(
                    f"❌ Failed to broadcast forwarded message: {e}"
                )
            
            # Send FCM notifications
            try:
                notify_conversation_participants(
                    conversation,
                    staff,
                    original_message.message,
                    exclude_sender=True
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to send FCM for forwarded message: {e}"
                )
            
            results.append({
                'conversation_id': conversation.id,
                'message_id': forwarded_msg.id,
                'created_conversation': False,
                'success': True
            })
            forwarded_to_existing += 1
            
            logger.info(
                f"✅ Forwarded to existing conversation {conv_id}"
            )
            
        except StaffConversation.DoesNotExist:
            results.append({
                'conversation_id': conv_id,
                'error': 'Conversation not found',
                'created_conversation': False,
                'success': False
            })
            logger.warning(
                f"❌ Conversation {conv_id} not found"
            )
        except Exception as e:
            results.append({
                'conversation_id': conv_id,
                'error': str(e),
                'created_conversation': False,
                'success': False
            })
            logger.error(
                f"❌ Error forwarding to conversation {conv_id}: {e}"
            )
    
    # Forward to new participants (create new conversations)
    for participant_id in new_participant_ids:
        try:
            participant = Staff.objects.get(
                id=participant_id,
                hotel=hotel,
                is_active=True
            )
            
            # Don't forward to self
            if participant.id == staff.id:
                results.append({
                    'participant_id': participant_id,
                    'error': 'Cannot forward message to yourself',
                    'created_conversation': False,
                    'success': False
                })
                continue
            
            # Get or create 1-on-1 conversation
            conversation, created = (
                StaffConversation.get_or_create_conversation(
                    hotel=hotel,
                    staff_list=[staff, participant],
                    title=''
                )
            )
            
            # Create forwarded message
            forwarded_msg = StaffChatMessage.objects.create(
                conversation=conversation,
                sender=staff,
                message=original_message.message,
                reply_to=None
            )
            
            # Update conversation timestamp
            conversation.has_unread = True
            conversation.save()
            
            # Broadcast the forwarded message
            message_serializer = StaffChatMessageSerializer(
                forwarded_msg,
                context={'request': request}
            )
            message_data = json.loads(
                json.dumps(
                    message_serializer.data,
                    cls=DjangoJSONEncoder
                )
            )
            
            # Remove sender-specific field before broadcasting
            if 'is_read_by_current_user' in message_data:
                del message_data['is_read_by_current_user']
            
            try:
                notification_manager.realtime_staff_chat_message_created(forwarded_msg)
            except Exception as e:
                logger.error(
                    f"❌ Failed to broadcast forwarded message: {e}"
                )
            
            # Send FCM notifications
            try:
                notify_conversation_participants(
                    conversation,
                    staff,
                    original_message.message,
                    exclude_sender=True
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to send FCM for forwarded message: {e}"
                )
            
            results.append({
                'conversation_id': conversation.id,
                'message_id': forwarded_msg.id,
                'created_conversation': created,
                'participant_id': participant_id,
                'success': True
            })
            forwarded_to_new += 1
            
            logger.info(
                f"✅ Forwarded to participant {participant_id} "
                f"(conversation {'created' if created else 'existing'})"
            )
            
        except Staff.DoesNotExist:
            results.append({
                'participant_id': participant_id,
                'error': 'Staff member not found or inactive',
                'created_conversation': False,
                'success': False
            })
            logger.warning(
                f"❌ Staff {participant_id} not found"
            )
        except Exception as e:
            results.append({
                'participant_id': participant_id,
                'error': str(e),
                'created_conversation': False,
                'success': False
            })
            logger.error(
                f"❌ Error forwarding to participant {participant_id}: {e}"
            )
    
    total_forwarded = forwarded_to_existing + forwarded_to_new
    
    logger.info(
        f"✅ FORWARD COMPLETE | Message: {message_id} | "
        f"Total: {total_forwarded} | "
        f"Existing: {forwarded_to_existing} | "
        f"New: {forwarded_to_new}"
    )
    
    return Response({
        'success': True,
        'forwarded_to_existing': forwarded_to_existing,
        'forwarded_to_new': forwarded_to_new,
        'total_forwarded': total_forwarded,
        'results': results
    }, status=status.HTTP_200_OK)
