from django.urls import path

from accounts.views import CurrentUserView, UserCreateView

app_name = "accounts"

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("users/", UserCreateView.as_view(), name="user-create"),
]