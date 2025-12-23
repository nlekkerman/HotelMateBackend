from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, time, timedelta
from django.utils import timezone
from typing import Dict, Optional


class CancellationCalculator:
    """
    Pure cancellation fee calculator service.
    
    Handles both DEFAULT mode (no policy) and POLICY mode calculations.
    Does not make external API calls - pure business logic only.
    """
    
    def __init__(self, booking):
        """Initialize calculator with a RoomBooking instance."""
        self.booking = booking
    
    def calculate(self) -> Dict:
        """
        Calculate cancellation fees and refunds.
        
        Returns:
            dict: {
                'fee_amount': Decimal,
                'refund_amount': Decimal,
                'description': str,
                'applied_rule': str,
                'is_default_mode': bool
            }
        """
        # DEFAULT mode - no policy assigned
        if not self.booking.cancellation_policy_id:
            return self._calculate_default_mode()
        
        # POLICY mode - use assigned policy
        return self._calculate_policy_mode()
    
    def _calculate_default_mode(self) -> Dict:
        """Calculate DEFAULT mode (legacy behavior preview)."""
        total_amount = self.booking.total_amount or Decimal('0.00')
        
        return {
            'fee_amount': Decimal('0.00'),
            'refund_amount': total_amount,
            'description': 'Default cancellation - no fee (preview only)',
            'applied_rule': 'DEFAULT_MODE',
            'is_default_mode': True
        }
    
    def _calculate_policy_mode(self) -> Dict:
        """Calculate POLICY mode using assigned cancellation policy."""
        policy = self.booking.cancellation_policy
        total_amount = self.booking.total_amount or Decimal('0.00')
        
        # Calculate hours until check-in
        hours_until_checkin = self._calculate_hours_until_checkin()
        
        # Handle different template types
        if policy.template_type == 'CUSTOM':
            return self._calculate_custom_policy(policy, total_amount, hours_until_checkin)
        else:
            return self._calculate_template_policy(policy, total_amount, hours_until_checkin)
    
    def _calculate_hours_until_checkin(self) -> float:
        """Calculate hours from now until check-in time."""
        now = timezone.now()
        
        # Default check-in time is 3:00 PM
        checkin_time = time(15, 0)  # 3:00 PM
        
        # TODO: If hotel has check-in time configuration, use that instead
        # checkin_time = self.booking.hotel.checkin_time or time(15, 0)
        
        # Combine check-in date with check-in time
        checkin_datetime = timezone.make_aware(
            datetime.combine(self.booking.check_in, checkin_time)
        )
        
        # Calculate time difference
        time_diff = checkin_datetime - now
        hours_until = time_diff.total_seconds() / 3600
        
        return max(0, hours_until)  # Don't return negative hours
    
    def _calculate_custom_policy(self, policy, total_amount: Decimal, hours_until_checkin: float) -> Dict:
        """Calculate fee using CUSTOM policy tiers."""
        # Find applicable tier (largest hours_before_checkin <= hours_until_checkin)
        applicable_tier = None
        
        for tier in policy.tiers.all():
            if tier.hours_before_checkin <= hours_until_checkin:
                if not applicable_tier or tier.hours_before_checkin > applicable_tier.hours_before_checkin:
                    applicable_tier = tier
        
        if not applicable_tier:
            # No applicable tier found - use most restrictive (shortest time)
            applicable_tier = policy.tiers.order_by('hours_before_checkin').first()
        
        if not applicable_tier:
            # No tiers defined - fallback to no penalty
            return {
                'fee_amount': Decimal('0.00'),
                'refund_amount': total_amount,
                'description': 'Custom policy with no applicable tiers',
                'applied_rule': 'CUSTOM_NO_TIERS',
                'is_default_mode': False
            }
        
        # Calculate fee based on applicable tier
        fee_amount = self._calculate_penalty_amount(
            applicable_tier.penalty_type,
            total_amount,
            applicable_tier.penalty_amount,
            applicable_tier.penalty_percentage
        )
        
        refund_amount = max(total_amount - fee_amount, Decimal('0.00'))
        
        return {
            'fee_amount': fee_amount,
            'refund_amount': refund_amount,
            'description': f'Custom policy tier: {applicable_tier.hours_before_checkin}h before check-in',
            'applied_rule': f'CUSTOM_TIER_{applicable_tier.id}',
            'is_default_mode': False
        }
    
    def _calculate_template_policy(self, policy, total_amount: Decimal, hours_until_checkin: float) -> Dict:
        """Calculate fee using template policy (FLEXIBLE, MODERATE, NON_REFUNDABLE)."""
        template_type = policy.template_type
        free_until_hours = policy.free_until_hours or 0
        
        # Check if we're in the free cancellation window
        if hours_until_checkin >= free_until_hours:
            return {
                'fee_amount': Decimal('0.00'),
                'refund_amount': total_amount,
                'description': f'Free cancellation ({template_type.lower()} policy)',
                'applied_rule': f'{template_type}_FREE',
                'is_default_mode': False
            }
        
        # Calculate penalty for late cancellation
        fee_amount = self._calculate_penalty_amount(
            policy.penalty_type,
            total_amount,
            policy.penalty_amount,
            policy.penalty_percentage
        )
        
        refund_amount = max(total_amount - fee_amount, Decimal('0.00'))
        
        return {
            'fee_amount': fee_amount,
            'refund_amount': refund_amount,
            'description': f'{template_type.lower().capitalize()} policy penalty',
            'applied_rule': f'{template_type}_PENALTY',
            'is_default_mode': False
        }
    
    def _calculate_penalty_amount(
        self, 
        penalty_type: str, 
        total_amount: Decimal, 
        penalty_amount: Optional[Decimal] = None,
        penalty_percentage: Optional[Decimal] = None
    ) -> Decimal:
        """Calculate penalty amount based on penalty type."""
        
        if penalty_type == 'FULL_STAY':
            return total_amount
        
        elif penalty_type == 'FIRST_NIGHT':
            return self._calculate_first_night_amount(total_amount)
        
        elif penalty_type == 'PERCENTAGE' and penalty_percentage:
            percentage_fee = total_amount * (penalty_percentage / Decimal('100'))
            return min(percentage_fee, total_amount)  # Cap at total amount
        
        elif penalty_type == 'FIXED' and penalty_amount:
            return min(penalty_amount, total_amount)  # Cap at total amount
        
        elif penalty_type == 'NONE':
            return Decimal('0.00')
        
        else:
            # Fallback - no penalty
            return Decimal('0.00')
    
    def _calculate_first_night_amount(self, total_amount: Decimal) -> Decimal:
        """
        Calculate first night amount.
        
        If booking has price breakdown, use first night.
        Otherwise, approximate as total_amount / nights with proper rounding.
        """
        # TODO: If booking has detailed price breakdown, use that
        # For now, approximate using total / nights
        
        nights = self.booking.nights
        if nights <= 0:
            return total_amount
        
        # Calculate per-night rate with proper decimal rounding
        per_night = (total_amount / Decimal(str(nights))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return per_night
    
    def calculate_no_show_penalty(self) -> Dict:
        """
        Calculate no-show penalty (separate from cancellation).
        
        Returns same format as calculate() method.
        """
        if not self.booking.cancellation_policy_id:
            # DEFAULT mode - typically full stay for no-show
            total_amount = self.booking.total_amount or Decimal('0.00')
            return {
                'fee_amount': total_amount,
                'refund_amount': Decimal('0.00'),
                'description': 'Default no-show penalty - full stay',
                'applied_rule': 'DEFAULT_NO_SHOW',
                'is_default_mode': True
            }
        
        policy = self.booking.cancellation_policy
        total_amount = self.booking.total_amount or Decimal('0.00')
        
        # Use no-show penalty type from policy
        if policy.no_show_penalty_type == 'SAME_AS_CANCELLATION':
            # Use the same logic as regular cancellation
            return self.calculate()
        
        elif policy.no_show_penalty_type == 'FIRST_NIGHT':
            fee_amount = self._calculate_first_night_amount(total_amount)
            
        elif policy.no_show_penalty_type == 'FULL_STAY':
            fee_amount = total_amount
            
        else:
            fee_amount = total_amount  # Default to full stay
        
        refund_amount = max(total_amount - fee_amount, Decimal('0.00'))
        
        return {
            'fee_amount': fee_amount,
            'refund_amount': refund_amount,
            'description': f'No-show penalty ({policy.no_show_penalty_type.lower()})',
            'applied_rule': f'NO_SHOW_{policy.no_show_penalty_type}',
            'is_default_mode': False
        }