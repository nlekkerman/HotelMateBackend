from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from hotel.models import Hotel
from rooms.models import RatePlan
from hotel.serializers import RatePlanSerializer, RatePlanListSerializer
from staff_chat.permissions import IsStaffMember


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsStaffMember])
def rate_plans_list(request, hotel_slug):
  
    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    if request.method == 'GET':
        rate_plans = RatePlan.objects.filter(hotel=hotel).select_related('cancellation_policy')
        serializer = RatePlanListSerializer(rate_plans, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RatePlanSerializer(
            data=request.data,
            context={'hotel': hotel}
        )
        if serializer.is_valid():
            rate_plan = serializer.save()
            return Response(
                RatePlanSerializer(rate_plan, context={'hotel': hotel}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsStaffMember])
def rate_plan_detail(request, hotel_slug, rate_plan_id):
    """
    GET: Retrieve rate plan details
    PUT/PATCH: Update rate plan (no DELETE - soft delete only)
    """
    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Ensure rate plan belongs to this hotel
    rate_plan = get_object_or_404(
        RatePlan.objects.select_related('cancellation_policy'),
        id=rate_plan_id,
        hotel=hotel
    )
    
    if request.method == 'GET':
        serializer = RatePlanSerializer(rate_plan, context={'hotel': hotel})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = RatePlanSerializer(
            rate_plan,
            data=request.data,
            partial=partial,
            context={'hotel': hotel}
        )
        if serializer.is_valid():
            updated_rate_plan = serializer.save()
            return Response(
                RatePlanSerializer(updated_rate_plan, context={'hotel': hotel}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffMember])
def rate_plan_delete(request, hotel_slug, rate_plan_id):
    """
    DELETE: Soft delete rate plan (return 405 to enforce soft delete policy)
    """
    return Response(
        {
            'error': 'Hard delete not allowed for rate plans',
            'message': 'Use PATCH with is_active=false to disable rate plan instead'
        },
        status=status.HTTP_405_METHOD_NOT_ALLOWED
    )