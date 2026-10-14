
from rest_framework.routers import DefaultRouter

from .views import CashCollectionViewSet, CashSubmissionViewSet
from .reconciliation_views import BankDepositViewSet


router = DefaultRouter()
router.register("collections", CashCollectionViewSet, basename="collection")
router.register(
    "cash-submissions",
    CashSubmissionViewSet,
    basename="cash-submission",
)
router.register(
    "bank-deposits",
    BankDepositViewSet,
    basename="bank-deposit",
)

urlpatterns = router.urls
