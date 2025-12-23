"""
Survey Analytics Services

Backend utility services for survey analytics and reporting.
These return raw numbers and data, not HTTP responses.

Usage:
    from hotel.services.survey_analytics import SurveyAnalytics
    
    analytics = SurveyAnalytics()
    avg_rating = analytics.avg_rating_for_hotel(hotel)
    completion_rate = analytics.completion_rate_for_period(hotel, start_date, end_date)
"""

from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from hotel.models import Hotel, RoomBooking, BookingSurveyResponse, HotelSurveyConfig


class SurveyAnalytics:
    """Internal service helpers for survey analytics"""
    
    def avg_rating_for_hotel(self, hotel, days_back=None):
        """
        Average overall rating for a hotel
        
        Args:
            hotel: Hotel instance
            days_back: Optional int, limit to last N days
            
        Returns:
            float or None: Average rating, None if no responses
        """
        queryset = BookingSurveyResponse.objects.filter(hotel=hotel)
        
        if days_back:
            cutoff_date = timezone.now() - timedelta(days=days_back)
            queryset = queryset.filter(submitted_at__gte=cutoff_date)
        
        result = queryset.aggregate(avg_rating=Avg('overall_rating'))
        return round(result['avg_rating'], 2) if result['avg_rating'] else None
    
    def completion_rate_for_period(self, hotel, start_date, end_date):
        """
        Survey completion rate for date range
        
        Args:
            hotel: Hotel instance
            start_date: datetime
            end_date: datetime
            
        Returns:
            dict: {'sent': int, 'completed': int, 'rate': float}
        """
        # Bookings completed in the period
        period_bookings = RoomBooking.objects.filter(
            hotel=hotel,
            checked_out_at__range=[start_date, end_date],
            status='COMPLETED'
        )
        
        sent_count = period_bookings.filter(survey_sent_at__isnull=False).count()
        completed_count = period_bookings.filter(survey_response__isnull=False).count()
        
        rate = (completed_count / sent_count * 100) if sent_count > 0 else 0
        
        return {
            'sent': sent_count,
            'completed': completed_count,
            'rate': round(rate, 1)
        }
    
    def response_count_by_send_mode(self, hotel=None, days_back=30):
        """
        Survey response counts grouped by send mode
        
        Args:
            hotel: Optional Hotel instance, None for all hotels
            days_back: int, days to look back
            
        Returns:
            dict: {'AUTO_IMMEDIATE': int, 'AUTO_DELAYED': int, 'MANUAL_ONLY': int}
        """
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        queryset = BookingSurveyResponse.objects.filter(\n            submitted_at__gte=cutoff_date\n        ).select_related('token_used')\n        \n        if hotel:\n            queryset = queryset.filter(hotel=hotel)\n        \n        # Group by the send mode from token snapshot\n        result = queryset.values('token_used__config_snapshot_send_mode').annotate(\n            count=Count('id')\n        )\n        \n        # Convert to dict with default values\n        send_mode_counts = {\n            'AUTO_IMMEDIATE': 0,\n            'AUTO_DELAYED': 0,\n            'MANUAL_ONLY': 0\n        }\n        \n        for item in result:\n            mode = item['token_used__config_snapshot_send_mode']\n            if mode in send_mode_counts:\n                send_mode_counts[mode] = item['count']\n        \n        return send_mode_counts\n    \n    def delayed_vs_immediate_effectiveness(self, hotel=None, days_back=30):\n        \"\"\"\n        Compare effectiveness of delayed vs immediate survey sending\n        \n        Args:\n            hotel: Optional Hotel instance\n            days_back: int, days to look back\n            \n        Returns:\n            dict: {\n                'immediate': {'sent': int, 'completed': int, 'avg_delay_hours': float},\n                'delayed': {'sent': int, 'completed': int, 'avg_delay_hours': float}\n            }\n        \"\"\"\n        cutoff_date = timezone.now() - timedelta(days=days_back)\n        \n        base_queryset = RoomBooking.objects.filter(\n            checked_out_at__gte=cutoff_date,\n            status='COMPLETED'\n        )\n        \n        if hotel:\n            base_queryset = base_queryset.filter(hotel=hotel)\n        \n        # Get immediate sends (survey_sent_at close to checked_out_at)\n        immediate_threshold = timedelta(hours=2)  # Within 2 hours = immediate\n        \n        immediate_bookings = base_queryset.filter(\n            survey_sent_at__isnull=False\n        ).extra(\n            where=[\"survey_sent_at - checked_out_at <= interval '2 hours'\"]\n        )\n        \n        delayed_bookings = base_queryset.filter(\n            survey_sent_at__isnull=False\n        ).extra(\n            where=[\"survey_sent_at - checked_out_at > interval '2 hours'\"]\n        )\n        \n        def calculate_stats(bookings):\n            sent = bookings.count()\n            completed = bookings.filter(survey_response__isnull=False).count()\n            \n            # Calculate average response delay\n            responses = bookings.filter(survey_response__isnull=False)\n            total_delay = 0\n            response_count = 0\n            \n            for booking in responses:\n                if booking.survey_response and booking.survey_response.response_delay_hours:\n                    total_delay += booking.survey_response.response_delay_hours\n                    response_count += 1\n            \n            avg_delay = total_delay / response_count if response_count > 0 else 0\n            \n            return {\n                'sent': sent,\n                'completed': completed,\n                'completion_rate': (completed / sent * 100) if sent > 0 else 0,\n                'avg_delay_hours': round(avg_delay, 1)\n            }\n        \n        return {\n            'immediate': calculate_stats(immediate_bookings),\n            'delayed': calculate_stats(delayed_bookings)\n        }\n    \n    def low_rating_bookings(self, hotel=None, days_back=30, rating_threshold=2):\n        \"\"\"\n        Get bookings with low ratings for attention\n        \n        Args:\n            hotel: Optional Hotel instance\n            days_back: int, days to look back\n            rating_threshold: int, ratings <= this value are considered low\n            \n        Returns:\n            QuerySet of BookingSurveyResponse with low ratings\n        \"\"\"\n        cutoff_date = timezone.now() - timedelta(days=days_back)\n        \n        queryset = BookingSurveyResponse.objects.filter(\n            overall_rating__lte=rating_threshold,\n            submitted_at__gte=cutoff_date\n        ).select_related('booking', 'hotel')\n        \n        if hotel:\n            queryset = queryset.filter(hotel=hotel)\n        \n        return queryset.order_by('submitted_at')\n\n\n# Canonical analytics keys (future-proof)\nSURVEY_ANALYTICS_KEYS = {\n    # Rating analytics\n    'overall_rating': 'overall_rating',\n    'avg_rating': 'hotel_avg_rating',\n    'rating_distribution': 'rating_dist',\n    \n    # Completion analytics\n    'completion_rate': 'completion_rate',\n    'response_count': 'response_count',\n    'send_count': 'send_count',\n    \n    # Timing analytics\n    'response_delay': 'response_delay_hours',\n    'send_delay': 'send_delay_hours',\n    \n    # Quality analytics\n    'low_rating_count': 'low_rating_count',\n    'low_rating_rate': 'low_rating_rate',\n    \n    # Mode analytics\n    'immediate_effectiveness': 'immediate_eff',\n    'delayed_effectiveness': 'delayed_eff',\n    'manual_effectiveness': 'manual_eff'\n}\n\n\ndef validate_analytics_key(key):\n    \"\"\"\n    Validate analytics key against canonical keys\n    Prevents ad-hoc naming drift\n    \"\"\"\n    if key not in SURVEY_ANALYTICS_KEYS.values():\n        raise ValueError(f\"Unknown analytics key '{key}'. Use canonical keys from SURVEY_ANALYTICS_KEYS\")\n    return True