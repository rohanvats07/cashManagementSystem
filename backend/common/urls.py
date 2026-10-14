from django.urls import path

from common.views import health_check

app_name = "common"

urlpatterns = [
    path("health/", health_check, name="health-check"),
]
