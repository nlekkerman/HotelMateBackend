from django.urls import path
from . import views

urlpatterns = [
    path('', views.cancellation_policies_list, name='cancellation-policy-list-create'),
    path('<int:policy_id>/', views.cancellation_policy_detail, name='cancellation-policy-detail'),
    path('templates/', views.cancellation_policy_templates, name='cancellation-policy-templates'),
]