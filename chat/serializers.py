# chat/serializers.py
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate

class CustomLoginSerializer(LoginSerializer):
    username = None  # Remove default username

    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(self.context['request'], email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        attrs['user'] = user
        return attrs
