from rest_framework.routers import DefaultRouter
from .views import HotelViewSet

router = DefaultRouter()
router.register(r'hotel_list', HotelViewSet)

urlpatterns = router.urls
