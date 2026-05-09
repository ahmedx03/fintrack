from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Handles PATCH /api/auth/me/ — allows changing email and/or password.

    Rules
    ─────
    • email       — optional; validated for uniqueness against other accounts
    • new_password — optional; must pass Django's AUTH_PASSWORD_VALIDATORS
    • current_password — required whenever new_password is supplied
    """
    current_password = serializers.CharField(write_only=True, required=False)
    new_password     = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )

    class Meta:
        model  = User
        fields = ('email', 'current_password', 'new_password')

    def validate_email(self, email):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            raise serializers.ValidationError("This email is already in use.")
        return email

    def validate(self, attrs):
        new_password     = attrs.get('new_password')
        current_password = attrs.get('current_password')
        if new_password and not current_password:
            raise serializers.ValidationError(
                {'current_password': 'Required when changing password.'}
            )
        if current_password and not self.instance.check_password(current_password):
            raise serializers.ValidationError(
                {'current_password': 'Incorrect password.'}
            )
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        instance = super().update(instance, validated_data)
        if new_password:
            instance.set_password(new_password)
            instance.save()
        return instance
