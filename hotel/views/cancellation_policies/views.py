from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from hotel.models import Hotel, CancellationPolicy
from hotel.serializers import (
    CancellationPolicySerializer,
    CancellationPolicyListSerializer
)
from staff_chat.permissions import IsStaffMember


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsStaffMember])
def cancellation_policies_list(request, hotel_slug):
    """
    GET: List all cancellation policies for a hotel
    POST: Create a new cancellation policy
    """
    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    if request.method == 'GET':
        policies = CancellationPolicy.objects.filter(hotel=hotel).prefetch_related('tiers')
        serializer = CancellationPolicyListSerializer(policies, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CancellationPolicySerializer(
            data=request.data,
            context={'hotel': hotel}
        )
        if serializer.is_valid():
            policy = serializer.save()
            # Return full policy with tiers
            response_serializer = CancellationPolicySerializer(policy)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsStaffMember])
def cancellation_policy_detail(request, hotel_slug, policy_id):
    """
    GET: Retrieve cancellation policy details
    PUT/PATCH: Update cancellation policy
    """
    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Ensure policy belongs to this hotel
    policy = get_object_or_404(
        CancellationPolicy.objects.prefetch_related('tiers'),
        id=policy_id,
        hotel=hotel
    )
    
    if request.method == 'GET':
        serializer = CancellationPolicySerializer(policy)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = CancellationPolicySerializer(
            policy,
            data=request.data,
            partial=partial,
            context={'hotel': hotel}
        )
        if serializer.is_valid():
            updated_policy = serializer.save()
            response_serializer = CancellationPolicySerializer(updated_policy)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffMember])
def cancellation_policy_templates(request):
    """
    GET: Return available cancellation policy templates and their validation rules
    """
    templates = {
        'FLEXIBLE': {
            'name': 'Flexible',
            'description': 'Free cancellation until X hours before check-in, then penalty',
            'required_fields': ['free_until_hours', 'penalty_type'],
            'penalty_type_options': ['FIRST_NIGHT', 'FULL_STAY']
        },
        'MODERATE': {
            'name': 'Moderate',
            'description': 'Free cancellation until X hours before check-in, then percentage or first night penalty',
            'required_fields': ['free_until_hours', 'penalty_type'],
            'penalty_type_options': ['FIRST_NIGHT', 'PERCENTAGE']
        },
        'NON_REFUNDABLE': {
            'name': 'Non-Refundable',
            'description': 'Full stay penalty (no refunds)',
            'required_fields': [],
            'penalty_type_options': ['FULL_STAY']
        },
        'CUSTOM': {
            'name': 'Custom Tiered',
            'description': 'Multiple penalty tiers based on hours before check-in',
            'required_fields': ['tiers'],
            'penalty_type_options': ['FIXED', 'PERCENTAGE', 'FIRST_NIGHT', 'FULL_STAY']
        }
    }
    
    return Response({
        'templates': templates,
        'penalty_types': [
            {'value': 'NONE', 'label': 'No Penalty'},
            {'value': 'FIXED', 'label': 'Fixed Amount'},
            {'value': 'PERCENTAGE', 'label': 'Percentage'},
            {'value': 'FIRST_NIGHT', 'label': 'First Night'},
            {'value': 'FULL_STAY', 'label': 'Full Stay'},
        ],
        'no_show_penalty_types': [
            {'value': 'SAME_AS_CANCELLATION', 'label': 'Same as Cancellation'},
            {'value': 'FIRST_NIGHT', 'label': 'First Night'},
            {'value': 'FULL_STAY', 'label': 'Full Stay'},
        ]
    })