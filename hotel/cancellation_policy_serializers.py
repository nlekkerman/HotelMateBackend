"""
Serializers for cancellation policy management.
"""
from rest_framework import serializers
from hotel.models import CancellationPolicy, CancellationPolicyTier


class CancellationPolicyTierSerializer(serializers.ModelSerializer):
    """Serializer for cancellation policy tiers."""
    
    class Meta:
        model = CancellationPolicyTier
        fields = ['id', 'hours_before_checkin', 'penalty_type', 'penalty_amount']


class CancellationPolicySerializer(serializers.ModelSerializer):
    """Detailed serializer for cancellation policies with nested tiers."""
    
    tiers = CancellationPolicyTierSerializer(many=True, required=False)
    
    class Meta:
        model = CancellationPolicy
        fields = [
            'id', 'name', 'template', 'free_until_hours', 'penalty_type',
            'penalty_amount', 'no_show_penalty_type', 'no_show_penalty_amount',
            'description', 'is_active', 'tiers'
        ]
        read_only_fields = ['id', 'hotel']
    
    def validate(self, attrs):
        """Validate cancellation policy based on template rules."""
        template = attrs.get('template')
        if not template:
            return attrs
        
        # Template-specific validation rules
        validation_rules = {
            'FLEXIBLE': {
                'required': ['free_until_hours', 'penalty_type'],
                'allowed_penalty_types': ['FIRST_NIGHT', 'FULL_STAY']
            },
            'MODERATE': {
                'required': ['free_until_hours', 'penalty_type'],
                'allowed_penalty_types': ['FIRST_NIGHT', 'PERCENTAGE']
            },
            'NON_REFUNDABLE': {
                'required': [],
                'fixed_values': {'penalty_type': 'FULL_STAY', 'free_until_hours': 0}
            },
            'CUSTOM': {
                'required': ['tiers'],
                'forbidden': ['free_until_hours', 'penalty_type', 'penalty_amount']
            }
        }
        
        rules = validation_rules.get(template)
        if not rules:
            return attrs
        
        # Check required fields
        for field in rules.get('required', []):
            if not attrs.get(field):
                if field == 'tiers':
                    tiers_data = attrs.get('tiers', [])
                    if not tiers_data:
                        raise serializers.ValidationError(f"Template {template} requires {field}")
                else:
                    raise serializers.ValidationError(f"Template {template} requires {field}")
        
        # Check allowed penalty types
        penalty_type = attrs.get('penalty_type')
        allowed_types = rules.get('allowed_penalty_types', [])
        if allowed_types and penalty_type and penalty_type not in allowed_types:
            raise serializers.ValidationError(
                f"Template {template} only allows penalty types: {', '.join(allowed_types)}"
            )
        
        # Apply fixed values for certain templates
        fixed_values = rules.get('fixed_values', {})
        for field, value in fixed_values.items():
            attrs[field] = value
        
        # Check forbidden fields for CUSTOM template
        forbidden = rules.get('forbidden', [])
        for field in forbidden:
            if attrs.get(field) is not None:
                raise serializers.ValidationError(
                    f"Template {template} does not allow {field} - use tiers instead"
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create policy with tiers and hotel scoping."""
        tiers_data = validated_data.pop('tiers', [])
        
        # Set hotel from context
        hotel = self.context.get('hotel')
        if not hotel:
            raise serializers.ValidationError("Hotel context is required")
        
        validated_data['hotel'] = hotel
        
        # Create the policy
        policy = CancellationPolicy.objects.create(**validated_data)
        
        # Create associated tiers
        for tier_data in tiers_data:
            CancellationPolicyTier.objects.create(policy=policy, **tier_data)
        
        return policy
    
    def update(self, instance, validated_data):
        """Update policy and replace all tiers."""
        tiers_data = validated_data.pop('tiers', [])
        
        # Update the policy fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Replace all tiers
        if 'tiers' in self.initial_data:  # Only if tiers were provided in request
            instance.tiers.all().delete()
            for tier_data in tiers_data:
                CancellationPolicyTier.objects.create(policy=instance, **tier_data)
        
        return instance


class CancellationPolicyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for policy list views."""
    
    tier_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CancellationPolicy
        fields = [
            'id', 'name', 'template', 'free_until_hours', 'penalty_type',
            'is_active', 'tier_count'
        ]
    
    def get_tier_count(self, obj):
        """Return the number of tiers for this policy."""
        return obj.tiers.count()