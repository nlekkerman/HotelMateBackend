from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffListViewSet, StaffConversationViewSet

router = DefaultRouter()

# Staff chat URLs are nested under hotel_slug
urlpatterns = [
    # Staff list for chat UI
    path(
        '<slug:hotel_slug>/staff-list/',
        StaffListViewSet.as_view({'get': 'list'}),
        name='staff-list'
    ),
    
    # Conversations
    path(
        '<slug:hotel_slug>/conversations/',
        StaffConversationViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='conversation-list'
    ),
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/',
        StaffConversationViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='conversation-detail'
    ),
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/send_message/',
        StaffConversationViewSet.as_view({'post': 'send_message'}),
        name='conversation-send-message'
    ),
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/mark_as_read/',
        StaffConversationViewSet.as_view({'post': 'mark_as_read'}),
        name='conversation-mark-as-read'
    ),
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/messages/',
        StaffConversationViewSet.as_view({'get': 'messages'}),
        name='conversation-messages'
    ),
]
