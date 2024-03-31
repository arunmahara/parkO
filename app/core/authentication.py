from django.db.models import Q
from django.contrib.auth import get_user_model

from rest_framework import status, serializers
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.services.api_response import generic_response


class TokenObtainSerializer(TokenObtainPairSerializer):
    """
    Overriding TokenObtainPairSerializer for email verification before obtaining JWT tokens (access and refresh).
    """

    def validate(self, attrs):
        username = attrs["username"]
        password = attrs["password"]

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(Q(email=username) | Q(username=username))
        except UserModel.DoesNotExist:
            raise serializers.ValidationError({
                "message": "Invalid Username!"
            })
        if not user.check_password(password):
            raise serializers.ValidationError({
                "message": "Invalid Password!"
            })

        return super().validate(attrs)


class TokenObtainPairView(TokenViewBase):
    """
    Return JWT tokens (access and refresh).
    """
    serializer_class = TokenObtainSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = response.data.get('access', None)
        if not token:
            return response
        return generic_response(
            success=True,
            message='Token Obtained Successfully',
            data=response.data,
            status=status.HTTP_200_OK
        )
