from rest_framework.routers import DefaultRouter
from .views import HotelViewSet

router = DefaultRouter()
router.register(r'hotels', HotelViewSet)

urlpatterns = router.urls
