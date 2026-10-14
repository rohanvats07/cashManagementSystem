from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from accounts.serializers import (
    UserCreateSerializer,
    UserProfileSerializer,
)
from common.permissions import IsCMRSAdmin


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsCMRSAdmin]