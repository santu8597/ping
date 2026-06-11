from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
from backend.users.models import CustomUser

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'email', 'is_active', 'last_login', 'is_faculty', 'designation']


class PackageMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPackageMaster
        fields = ["id", "package_name", "package_description", "package_points", "package_amount", "package_duration"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    package = PackageMasterSerializer()

    class Meta:
        model = UserSubscription
        fields = ['id', 'total_points', 'used_points', 'earn_points', 'remaining_points', 'package_activation_date',
                  'insert_status', 'command_name', 'run_time', 'package_deactivation_date', 'user', 'package',
                  'created_date']


class UserSubscriptionListSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserSubscription
        fields = ['id', 'total_points', 'used_points', 'total_points', 'remaining_points', 'user']
