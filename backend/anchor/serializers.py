import base64
from django.contrib.auth.models import Group,GroupManager
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import *
from backend.users.models import UsersHostGroup, UsersZone
from datetime import datetime

from ..common.serializers import ClusterLocationNodeSerializer


class CommandViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommendMaster
        fields = "__all__"

class BlockCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommendMaster
        fields = "__all__"

class RunCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommendMaster
        fields = "__all__"

class HostGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersHostGroup
        fields = "__all__"

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersZone
        fields = "__all__"

class UserAnchorDetailsSerializer(serializers.ModelSerializer):
    anchor_details = serializers.SerializerMethodField()
    class Meta:
        model = UserAnchor
        fields  = ['id','anchor_id', 'location', 'latitude','longitude','address', 'anchor_details']
    def get_anchor_details(self,UserAnchor):
        rs = Anchor.objects.filter(id = UserAnchor.anchor_id)
        anchor = AnchorSerializer(rs, many=True)
        return anchor.data


class HistoryDetailsSerializer(serializers.ModelSerializer):
    users_host_group = HostGroupSerializer()
    users_zone = ZoneSerializer()
    user_anchor = UserAnchorDetailsSerializer()
    class Meta:
        model = CommendExecutionHistoryDetails
        fields = "__all__"

class CommandHitRequestHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommendExecutionHistory
        fields = "__all__"

class QueryReportsSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = CommendExecutionHistory
        fields = [
            'id',
            'server_hit_status',
            'check_points_status',
            'query_type',
            'query_status',
            'created_date',
            'query_execution_end_date',
            'has_been_seen',
            'host_name',
            'hosts',
            'service_name',
            'anchor_names',
            'zone_area_name',
            'region',
            'query',
            'commend_query_id',
            'dnsquery_type',
            'query_execution_interval_unit',
            'query_execution_interval_time',
            'is_public',
            'user_id',
            'user_email',
            'full_name'
            ]
    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return None

class CommandHistoryDetailsSerializer(serializers.ModelSerializer):
    query_details = serializers.SerializerMethodField()
    class Meta:
        model = CommendExecutionHistory
        fields = "__all__"
    def get_query_details(self,CommendExecutionHistory):
        rs = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id = CommendExecutionHistory.id, user_id=CommendExecutionHistory.user_id)
        history = HistoryDetailsSerializer(rs, many=True)
        return history.data

class AnchorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anchor
        fields = "__all__"

class UserAnchorSerializer(serializers.ModelSerializer):
    anchor_details = serializers.SerializerMethodField()
    class Meta:
        model = UserAnchor
        fields = "__all__"
    def get_anchor_details(self,UserAnchor):
        rs = Anchor.objects.filter(id = UserAnchor.anchor_id)
        anchor = AnchorSerializer(rs, many=True)
        return anchor.data

class UserAnchorGroupBySerializer(serializers.ModelSerializer):
    # anchor_details = serializers.SerializerMethodField()
    class Meta:
        model = UserAnchor
        # fields = "__all__"
        fields = [
            'id',
            'location'
            ]
    # def get_anchor_details(self,UserAnchor):
    #     rs = Anchor.objects.filter(id = UserAnchor.anchor_id)
    #     anchor = AnchorSerializer(rs, many=True)
    #     return anchor.data

class AnchorMapCoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupWiseAncherLocationLabel
        fields = ['id', 'parent_id', 'label_type', 'regiser_anchor_count', 'center_latitude', 'center_longitude']


class AnchorQrCodeSerializer(serializers.ModelSerializer):
    lease_details = serializers.SerializerMethodField()
    class Meta:
        model = AnchorQrCode
        fields = "__all__"
    def get_lease_details(self,AnchorQrCode):
        rs = UserAnchor.objects.filter(anchor_qr_code_id = AnchorQrCode.id, user_id=AnchorQrCode.user_id)
        lease = UserAnchorSerializer(rs, many=True)
        return lease.data

class UserAnchorListSerializer(serializers.ModelSerializer):
    anchor = serializers.SerializerMethodField()
    class Meta:
        model = UserAnchor
        fields = "__all__"
    def get_anchor(self,UserAnchor):
        rs = Anchor.objects.filter(id = UserAnchor.anchor_id).first()
        anchor = AnchorSerializer(rs)
        return anchor.data

class IpDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServeIpDetails
        # fields = "__all__"
        fields  = ['serve_location','address', 'country', 'state','city','postal', 'latitude','longitude','ip','org']

class LatencyCheckHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LatencyCheckHistory
        # fields = "__all__"
        fields  = ['id','serve_ip_details', 'latency_check_domain_name']

class LatencyCheckHistoryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatencyCheckHistoryDetails
        # fields = "__all__"
        fields = ['id', 'latency_check_domain_name']


class QueryStatsSerializer(serializers.Serializer):
    query = serializers.CharField()
    total_queries = serializers.IntegerField()

class ActiveAnchorNetworkSerializer(serializers.ModelSerializer):

    anchor_details = serializers.SerializerMethodField()
    network_details = serializers.SerializerMethodField()
    user_anchor_details = serializers.SerializerMethodField()

    class Meta:
        model = AnchorIpDetails
        fields = [
            "id",
            "anchor_id",
            "anchor_name",
            "user_anchor_id",
            "status",
            "last_seen",
            "created_at",
            "updated_at",

            "anchor_details",
            "network_details",
            "user_anchor_details",
        ]

    # -------------------------
    # Anchor Details
    # -------------------------
    def get_anchor_details(self, obj):

        user_anchors = UserAnchor.objects.filter(
            id=obj.user_anchor_id,
            is_deleted=False,
            is_blocked=False,
            status="active",
            anchor_id__is_online=True
        ).select_related("anchor")

        anchors = []

        for ua in user_anchors:
            if ua.anchor:
                anchors.append(ua.anchor)

        return AnchorSerializer(anchors, many=True).data


    # -------------------------
    # Network Details
    # -------------------------
    def get_network_details(self, obj):

        return {
            "ip_address": obj.ip_address,
            "asn": obj.asn,
            "isp": obj.isp,
            "isp_location": obj.isp_location,
            "status": obj.status,
            "last_seen": obj.last_seen,
        }


    # -------------------------
    # UserAnchor Details
    # -------------------------
    def get_user_anchor_details(self, obj):

        ua = UserAnchor.objects.filter(
            id=obj.user_anchor_id,
            is_deleted=False,
            is_blocked=False,
        ).select_related("user", "anchor").first()

        if not ua:
            return None

        return {
            "id": ua.id,
            "user_id": ua.user_id,
            "status": ua.status,
            "lease_id": ua.lease_id,
            "location": ua.location
        }
class MeasurementSerializer(serializers.ModelSerializer):

    server_ip = serializers.CharField(write_only=True)

    class Meta:
        model = Measurement
        fields = [
            "id",
            "anchor_ip_id",
            "cluster_ip_id",
            "command_id",
            "timestamp",
            "min_latency",
            "avg_latency",
            "max_latency",
            "status",
            "error_message",
            "server_ip",   # virtual field
        ]

        read_only_fields = ["id", "timestamp", "cluster_ip_id"]

    def create(self, validated_data):

        server_ip = validated_data.pop("server_ip")

        try:
            cluster = ClusterLocationNode.objects.get(
                cluster_ip=server_ip,
                status="ACTIVE"
            )
        except ClusterLocationNode.DoesNotExist:
            raise serializers.ValidationError(
                {"server_ip": "Invalid or inactive cluster IP"}
            )

        validated_data["cluster_ip_id"] = cluster

        return super().create(validated_data)

class MeasurementByIPSerializer(serializers.ModelSerializer):

    anchor_ip_id = ActiveAnchorNetworkSerializer(read_only=True)
    cluster_ip_id = ClusterLocationNodeSerializer(read_only=True)
    class Meta:
        model = Measurement
        fields = "__all__"
