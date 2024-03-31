from rest_framework import serializers
from .models import User, ParkSlot, Rating
from django.db.models import Avg


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role_type', 'profilePic', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class ParkSlotSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()

    class Meta:
        model = ParkSlot
        fields = ['id', 'status', 'price', 'address', 'coordinates', 'description', 'type', 'picture', 'rating']

    def get_rating(self, obj):
        ratings = list(Rating.objects.filter(slot=obj).values_list('rating', flat=True))
        if ratings:
            return sum(ratings) / len(ratings)
        return 0
