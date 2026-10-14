from rest_framework.routers import DefaultRouter

from loans.views import LoanViewSet

app_name = "loans"

router = DefaultRouter()
router.register("loans", LoanViewSet, basename="loan")

urlpatterns = router.urls