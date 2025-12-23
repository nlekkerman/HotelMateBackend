from django.urls import path
from . import views

urlpatterns = [
    path('', views.rate_plans_list, name='rate-plan-list-create'),
    path('<int:rate_plan_id>/', views.rate_plan_detail, name='rate-plan-detail'),
    path('<int:rate_plan_id>/delete/', views.rate_plan_delete, name='rate-plan-delete'),
]