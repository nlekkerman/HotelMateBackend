from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import (
    StaffConversation, StaffChatMessage, StaffChatAttachment
)
from .serializers import (
    StaffListSerializer,
    StaffConversationSerializer,
    StaffConversationDetailSerializer,
    StaffChatMessageSerializer,
)
from staff.models import Staff
from hotel.models import Hotel


class StaffListPagination(PageNumberPagination):
    """
    Custom pagination for staff list
    Supports infinite scroll with 50 items per page
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class StaffListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing staff members for chat UI
    GET /api/staff-chat/<hotel_slug>/staff-list/
    
    Supports pagination for infinite scroll:
    - Default: 50 staff per page
    - Query params: ?page=2, ?page_size=100
    - Search: ?search=John
    """
    serializer_class = StaffListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaffListPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'first_name', 'last_name', 'email',
        'department__name', 'role__name'
    ]
    ordering_fields = ['first_name', 'last_name', 'department__name']
    ordering = ['first_name', 'last_name']

    def get_queryset(self):
        """
        Return all active staff for the current user's hotel
        """
        user = self.request.user
        hotel_slug = self.kwargs.get('hotel_slug')

        if not hotel_slug:
            return Staff.objects.none()

        try:
            # Verify the requesting user belongs to this hotel
            requesting_staff = Staff.objects.get(user=user)
            if requesting_staff.hotel.slug != hotel_slug:
                return Staff.objects.none()
        except Staff.DoesNotExist:
            return Staff.objects.none()

        # Return all staff from the same hotel, excluding the current user
        return Staff.objects.filter(
            hotel__slug=hotel_slug,
            is_active=True
        ).select_related('department', 'role', 'hotel').exclude(
            user=user
        )


class StaffConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing staff conversations
    
    Endpoints:
    - GET /api/staff-chat/<hotel_slug>/conversations/ - List conversations
    - POST /api/staff-chat/<hotel_slug>/conversations/ - Create conversation
    - GET /api/staff-chat/<hotel_slug>/conversations/{id}/ - Get details
    - POST /api/staff-chat/<hotel_slug>/conversations/{id}/send_message/
    - POST /api/staff-chat/<hotel_slug>/conversations/{id}/mark_as_read/
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'participants__first_name']
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StaffConversationDetailSerializer
        return StaffConversationSerializer

    def get_queryset(self):
        """
        Return conversations for the current user's hotel
        """
        user = self.request.user
        hotel_slug = self.kwargs.get('hotel_slug')

        if not hotel_slug:
            return StaffConversation.objects.none()

        try:
            staff = Staff.objects.get(user=user)
            if staff.hotel.slug != hotel_slug:
                return StaffConversation.objects.none()

            # Return conversations where the user is a participant
            return StaffConversation.objects.filter(
                hotel__slug=hotel_slug,
                participants=staff
            ).select_related('hotel').prefetch_related(
                'participants',
                'messages'
            ).distinct()

        except Staff.DoesNotExist:
            return StaffConversation.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Create a new conversation
        Expects: participant_ids (list of staff IDs)
        """
        hotel_slug = kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        try:
            current_staff = Staff.objects.get(user=request.user)
            if current_staff.hotel != hotel:
                return Response(
                    {'error': 'You can only create conversations '
                              'in your hotel'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        participant_ids = request.data.get('participant_ids', [])

        if not participant_ids:
            return Response(
                {'error': 'At least one participant is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify all participants are from the same hotel
        participants = Staff.objects.filter(
            id__in=participant_ids,
            hotel=hotel,
            is_active=True
        )

        if participants.count() != len(participant_ids):
            return Response(
                {'error': 'Some participants are invalid or inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build complete staff list (current user + other participants)
        title = request.data.get('title', '')
        staff_list = [current_staff] + list(participants)
        
        # Get or create conversation (enforces 1-on-1 uniqueness)
        conversation, created = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list,
            title=title
        )

        serializer = self.get_serializer(conversation)
        response_status = (
            status.HTTP_201_CREATED if created
            else status.HTTP_200_OK
        )

        return Response(serializer.data, status=response_status)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None, hotel_slug=None):
        """
        Send a message in a conversation
        POST /api/staff-chat/<hotel_slug>/conversations/{id}/send_message/
        Body: {
            "message": "Hello!",
            "reply_to": <message_id> (optional)
        }
        """
        conversation = self.get_object()

        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify staff is a participant
        if staff not in conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        message_text = request.data.get('message', '').strip()
        reply_to_id = request.data.get('reply_to')

        if not message_text:
            return Response(
                {'error': 'Message cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the message
        message_data = {
            'conversation': conversation.id,
            'sender': staff.id,
            'message': message_text,
        }

        if reply_to_id:
            message_data['reply_to'] = reply_to_id

        message = StaffChatMessage.objects.create(
            conversation=conversation,
            sender=staff,
            message=message_text,
            reply_to_id=reply_to_id if reply_to_id else None
        )

        # Update conversation timestamp
        conversation.save()

        serializer = StaffChatMessageSerializer(
            message,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None, hotel_slug=None):
        """
        Mark all messages in conversation as read by current user
        POST /api/staff-chat/<hotel_slug>/conversations/{id}/mark_as_read/
        """
        conversation = self.get_object()

        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark all unread messages as read
        unread_messages = conversation.messages.filter(
            is_deleted=False
        ).exclude(sender=staff).exclude(read_by=staff)

        for message in unread_messages:
            message.read_by.add(staff)
            if not message.is_read:
                message.is_read = True
                message.save(update_fields=['is_read'])

        return Response(
            {'message': f'Marked {unread_messages.count()} messages as read'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None, hotel_slug=None):
        """
        Get all messages in a conversation
        GET /api/staff-chat/<hotel_slug>/conversations/{id}/messages/
        """
        conversation = self.get_object()

        messages = conversation.messages.filter(
            is_deleted=False
        ).select_related('sender').prefetch_related(
            'attachments', 'read_by'
        ).order_by('timestamp')

        serializer = StaffChatMessageSerializer(
            messages,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def for_forwarding(self, request, hotel_slug=None):
        """
        Get conversations list optimized for forwarding UI
        GET /api/staff-chat/<hotel_slug>/conversations/for-forwarding/
        
        Returns a simplified list of conversations with:
        - conversation id, title, participants
        - last message preview
        - is_group flag
        
        Supports search: ?search=John
        """
        user = request.user
        hotel_slug = self.kwargs.get('hotel_slug')

        if not hotel_slug:
            return Response(
                {'error': 'Hotel slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            staff = Staff.objects.get(user=user)
            if staff.hotel.slug != hotel_slug:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get conversations
        conversations = StaffConversation.objects.filter(
            hotel__slug=hotel_slug,
            participants=staff
        ).select_related('hotel').prefetch_related(
            'participants'
        ).distinct().order_by('-updated_at')
        
        # Apply search filter if provided
        search = request.query_params.get('search', '').strip()
        if search:
            conversations = conversations.filter(
                Q(title__icontains=search) |
                Q(participants__first_name__icontains=search) |
                Q(participants__last_name__icontains=search)
            ).distinct()
        
        # Build simplified response
        results = []
        for conv in conversations:
            # Get other participant(s)
            other_participants = conv.participants.exclude(id=staff.id)
            
            # Build title
            if conv.is_group:
                title = conv.title or f"Group ({conv.participants.count()})"
            else:
                other = other_participants.first()
                if other:
                    title = f"{other.first_name} {other.last_name}".strip()
                else:
                    title = "Unknown"
            
            # Get last message
            last_msg = conv.messages.filter(
                is_deleted=False
            ).order_by('-timestamp').first()
            
            last_message_preview = None
            if last_msg:
                last_message_preview = {
                    'message': last_msg.message[:50],
                    'timestamp': last_msg.timestamp,
                    'sender_name': (
                        f"{last_msg.sender.first_name} "
                        f"{last_msg.sender.last_name}"
                    ).strip()
                }
            
            # Get participant info
            participants_info = []
            for p in other_participants:
                participants_info.append({
                    'id': p.id,
                    'name': f"{p.first_name} {p.last_name}".strip(),
                    'profile_image_url': (
                        p.profile_image.url if p.profile_image and
                        hasattr(p.profile_image, 'url') else None
                    )
                })
            
            results.append({
                'id': conv.id,
                'title': title,
                'is_group': conv.is_group,
                'participants': participants_info,
                'participant_count': conv.participants.count(),
                'last_message': last_message_preview,
                'updated_at': conv.updated_at
            })
        
        return Response({
            'count': len(results),
            'conversations': results
        })
