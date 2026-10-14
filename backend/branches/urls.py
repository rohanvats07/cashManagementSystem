from rest_framework.routers import DefaultRouter

from branches.views import BranchViewSet

app_name = "branches"

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")

urlpatterns = router.urls