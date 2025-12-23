"""
Cancellation Policy and Rate Plan Management URLs

These URLs are included in staff_urls.py under:
/api/staff/hotel/{hotel_slug}/

Hotel_slug MUST NOT appear in these patterns since it's captured by the parent.
"""

from django.urls import path
from hotel.views.cancellation_policies import (
    cancellation_policies_list,
    cancellation_policy_detail,
    cancellation_policy_templates
)
from hotel.views.rate_plans import (
    rate_plans_list,
    rate_plan_detail,
    rate_plan_delete
)

# Combined URL patterns for both cancellation policies and rate plans
urlpatterns = [
    # Cancellation Policy URLs - will be prefixed with cancellation-policies/
    # Rate Plan URLs - will be prefixed with rate-plans/
]

# Separate URL patterns for different prefixes
cancellation_policy_urlpatterns = [
    path('', cancellation_policies_list, name='list'),
    path('templates/', cancellation_policy_templates, name='templates'), 
    path('<int:policy_id>/', cancellation_policy_detail, name='detail'),
]

rate_plan_urlpatterns = [
    path('', rate_plans_list, name='list'),
    path('<int:rate_plan_id>/', rate_plan_detail, name='detail'),
    path('<int:rate_plan_id>/delete/', rate_plan_delete, name='delete'),
]