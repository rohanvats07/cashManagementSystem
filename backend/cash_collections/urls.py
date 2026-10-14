
from rest_framework.routers import DefaultRouter

from .views import CashCollectionViewSet, CashSubmissionViewSet


router = DefaultRouter()
router.register("collections", CashCollectionViewSet, basename="collection")
router.register(
    "cash-submissions",
    CashSubmissionViewSet,
    basename="cash-submission",
)

urlpatterns = router.urls
