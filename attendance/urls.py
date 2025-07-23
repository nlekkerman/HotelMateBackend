# attendance/urls.py
from rest_framework.routers import DefaultRouter
from .views import ClockLogViewSet
router = DefaultRouter()
router.register('clock-logs', ClockLogViewSet, basename='clock-log')

urlpatterns = router.urls
