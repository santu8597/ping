from backend.users.models import CustomUser
from .models import *
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'email', 'is_active', 'last_login']


class CountryViewSerializer(serializers.Serializer):
    class Meta:
        model = Countries
        fields = "__all__"

    # name = serializers.CharField(max_length=250)

    def create(self, validated_data):
        country_obj = Country(**validated_data)
        country_obj.save()
        return country_obj

    def update(self, instance, validated_data):
        instance.name = validated_data["name"]
        instance.save()
        return instance

    ##class StateViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = "__all__"

    ##class CityViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cities
        fields = "__all__"


class CountryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Countries
        fields = ['id', 'country_name', 'country_code', 'country_iso_code']


class StateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = ['id', 'state_code', 'state_name', 'country_id']


class CityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cities
        fields = ['id', 'city_name', 'country_id', 'state_id']


class UserGroupMastersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroupMasters
        fields = "__all__"


class MenuMastersListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuMasters
        fields = ['id', 'parent_id', 'menu_name']


class MenuMastersSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuMasters
        fields = "__all__"


class UserGroupSerializer(serializers.ModelSerializer):
    group = UserGroupMastersSerializer()
    user = UserSerializer()

    class Meta:
        model = UserGroup
        fields = "__all__"


class TemplatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Templates
        fields = "__all__"


class ResearchPageLayoutsSerializer(serializers.ModelSerializer):
    template = serializers.SerializerMethodField()

    class Meta:
        model = ResearchPageLayouts
        fields = "__all__"

    def get_template(self, ResearchPageLayouts):
        rs = Templates.objects.filter(id=ResearchPageLayouts.template_id).first()
        template = TemplatesSerializer(rs)
        return template.data


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultSiteSetup
        fields = "__all__"

class ClusterLocationNodeSerializer(serializers.ModelSerializer):
    userName = serializers.SerializerMethodField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    class Meta:
        model = ClusterLocationNode
        fields = [
            "id",
            "name",
            "cluster_ip",
            "location",
            "latitude",
            "longitude",
            "status",
            "userName"
        ]

    def get_userName(self, obj):
        return "Active" if obj.status == "ACTIVE" else "INACTIVE"