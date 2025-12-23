"""
Serializers for rate plan management with cancellation policy support.
"""
from rest_framework import serializers
from rooms.models import RatePlan
from hotel.cancellation_policy_serializers import CancellationPolicyListSerializer


class RatePlanSerializer(serializers.ModelSerializer):
    """Serializer for rate plans with cancellation policy support."""
    
    cancellation_policy_detail = CancellationPolicyListSerializer(
        source='cancellation_policy', read_only=True
    )
    
    class Meta:
        model = RatePlan
        fields = [
            'id', 'name', 'code', 'description', 'is_refundable',
            'default_discount_percent', 'is_active', 'cancellation_policy',
            'cancellation_policy_detail'
        ]
        read_only_fields = ['id']
    
    def validate_code(self, value):
        """Auto-uppercase rate plan code."""
        return value.upper() if value else value
    
    def validate(self, attrs):
        """Validate rate plan fields."""
        hotel = self.context.get('hotel')
        
        # Ensure cancellation_policy belongs to the same hotel
        cancellation_policy = attrs.get('cancellation_policy')
        if cancellation_policy and cancellation_policy.hotel != hotel:
            raise serializers.ValidationError(
                "Cancellation policy must belong to the same hotel"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create rate plan with hotel scoping."""
        validated_data['hotel'] = self.context['hotel']
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update rate plan with hotel scoping."""
        validated_data['hotel'] = self.context['hotel']
        return super().update(instance, validated_data)


class RatePlanListSerializer(serializers.ModelSerializer):
    """Simplified serializer for rate plan list views."""
    
    cancellation_policy_name = serializers.CharField(
        source='cancellation_policy.name', read_only=True
    )
    
    class Meta:
        model = RatePlan
        fields = [
            'id', 'name', 'code', 'description', 'is_refundable',
            'is_active', 'cancellation_policy_name'
        ]