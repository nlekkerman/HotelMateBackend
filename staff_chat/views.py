from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Max
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


class StaffListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing staff members for chat UI
    GET /api/staff-chat/<hotel_slug>/staff-list/
    """
    serializer_class = StaffListSerializer
    permission_classes = [permissions.IsAuthenticated]
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

        # Check if a conversation already exists with these participants
        # For 1-on-1 conversations
        if len(participant_ids) == 1:
            existing_conversation = StaffConversation.objects.filter(
                hotel=hotel,
                is_group=False,
                participants=current_staff
            ).filter(
                participants__id=participant_ids[0]
            ).annotate(
                participant_count=Max('participants__id')
            ).filter(participant_count=2).first()

            if existing_conversation:
                serializer = self.get_serializer(existing_conversation)
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )

        # Create new conversation
        title = request.data.get('title', '')
        conversation = StaffConversation.objects.create(
            hotel=hotel,
            title=title,
            created_by=current_staff,
            has_unread=False
        )

        # Add participants (including current user)
        conversation.participants.add(current_staff)
        for participant in participants:
            conversation.participants.add(participant)

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
