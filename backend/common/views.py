from django.db import connection
from django.db.utils import DatabaseError

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return Response(
            {
                "status": "ok",
                "service": "cmrs-api",
                "database": "connected",
            },
            status=status.HTTP_200_OK,
        )
    except DatabaseError:
        return Response(
            {
                "status": "error",
                "service": "cmrs-api",
                "database": "unavailable",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )