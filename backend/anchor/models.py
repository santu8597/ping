from django.db import models
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from django.db.models import JSONField

from backend.common.models import ClusterLocationNode
from backend.users.models import *


# Create your models here.
class CommendMaster(models.Model):
    commend_name = models.CharField(max_length=255, null=True)
    commend_description = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                   related_name='commend_created_user_id', null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    action = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'commend_master'


class CommendExecutionHistory(models.Model):
    hit_status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('success', 'success')
    )
    point_status_choices = (
        ('insufficient point', 'insufficient point'),
        ('not detected', 'not detected'),
        ('failure', 'failure'),
        ('success', 'success')
    )
    query_type_status_choices = (
        ('regular', 'regular'),
        ('domain_zone_regular', 'domain_zone_regular'),
        ('domain_anchor_periodic', 'domain_anchor_periodic'),
        ('domain_zone_periodic', 'domain_zone_periodic'),
        ('service_anchor_periodic', 'service_anchor_periodic'),
        ('service_zone_periodic', 'service_zone_periodic'),
        ('periodic', 'periodic'),
        ('traceroute', 'traceroute'),
        ('domain_anchor_traceroute', 'domain_anchor_traceroute'),
        ('domain_zone_traceroute', 'domain_zone_traceroute'),
        ('domain_anchor_dnsquery', 'domain_anchor_dnsquery'),
        ('domain_zone_dnsquery', 'domain_zone_dnsquery'),
        ('constant', 'constant')
    )
    query_execution_status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('close', 'close'),
        ('enqueue', 'enqueue')
    )
    query_execution_interval_unit_choices = (
        ('second', 'second'),
        ('minute', 'minute'),
        ('hour', 'hour')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False},
                             related_name='history_user_id', null=True)
    commend_query_id = models.CharField(max_length=255, null=True, blank=True)
    commend_request_payload = JSONField(default=dict)
    server_hit_status = models.CharField(max_length=100, choices=hit_status_choices, default='running')
    check_points_status = models.CharField(max_length=100, choices=point_status_choices, default='success')
    query_type = models.CharField(max_length=100, choices=query_type_status_choices, default='regular')
    query_status = models.CharField(max_length=100, choices=query_execution_status_choices, default='running')
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    query_execution_end_date = models.DateTimeField(default=timezone.now)
    has_been_seen = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    host_ids = JSONField(default=list, blank=True, null=True)
    host_name = models.CharField(max_length=255, null=True, blank=True)
    hosts = models.CharField(max_length=255, null=True, blank=True)
    service_id = JSONField(default=list, blank=True, null=True)
    service_name = models.CharField(max_length=255, null=True, blank=True)
    service_domain_ids = JSONField(default=list, blank=True, null=True)
    zone_id = JSONField(default=list, blank=True, null=True)
    zone_area_name = models.CharField(max_length=255, null=True, blank=True)
    anchor_ids = JSONField(default=list, blank=True, null=True)
    anchor_names = models.CharField(max_length=255, null=True, blank=True)
    dnsquery_type = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    query = models.CharField(max_length=50, null=True, blank=True)
    query_execution_interval_unit = models.CharField(max_length=50, choices=query_execution_interval_unit_choices,
                                                     default='second')
    query_execution_interval_time = models.IntegerField(default=10, null=True)
    last_query_execution_data_sheen_time = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = 'commend_execution_history'


class Anchor(models.Model):
    anchor_name = models.CharField(max_length=255, blank=True, null=True)
    anchor_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    anchor_status = models.CharField(max_length=100, blank=True, null=True)
    server_url = models.CharField(max_length=255, blank=True, null=True)
    db_url = models.CharField(max_length=255, blank=True, null=True)
    storage_db = models.CharField(max_length=255, blank=True, null=True)
    version = models.IntegerField(default=0, null=True)
    anchor_created_date = models.DateTimeField(default=datetime.now, blank=True)
    anchor_updated_at = models.DateTimeField(default=datetime.now, blank=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    ip_type = models.CharField(max_length=50, blank=True, null=True)
    public_ip = models.CharField(max_length=100, blank=True, null=True)
    ip_v6 = models.CharField(max_length=255, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'anchor'


class AnchorQrCode(models.Model):
    register_choices = (
        ('no', 'no'),
        ('yes', 'yes')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False}, related_name='anchor_qrcode',
                             null=True)
    anchor_qrcode_file = models.CharField(max_length=255, blank=True, null=True)
    decoded_qrcode = models.TextField(blank=True, null=True)
    is_registered = models.CharField(max_length=50, choices=register_choices, default='no')
    complete_regis = models.CharField(max_length=50, choices=register_choices, default='no')
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'anchor_qrcode'


class UserAnchor(models.Model):
    register_choices = (
        ('requested', 'requested'),
        ('accepted', 'accepted'),
        ('active', 'active')
    )

    location_register_choices = (
        ('notregistered', 'notregistered'),
        ('processing', 'processing'),
        ('registered', 'registered'),
        ('failure', 'failure')
    )
    anchor = models.ForeignKey(Anchor, on_delete=models.CASCADE,
                               limit_choices_to={'is_blocked': False, 'is_deleted': False},
                               related_name='user_anchor_id', null=True)
    anchor_qr_code = models.ForeignKey(AnchorQrCode, on_delete=models.CASCADE, limit_choices_to={'is_deleted': False},
                                       related_name='user_qr_code', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False}, related_name='anchor_user_id',
                             null=True)
    anchor_qrcode_file = models.CharField(max_length=255, blank=True, null=True)
    decoded_qrcode = models.TextField(blank=True, null=True)
    lease_id = models.CharField(max_length=255, blank=True, null=True)
    aiori_anchor_id = models.CharField(max_length=255, null=True)
    lease_from_date = models.DateTimeField(default=datetime.now, blank=True)
    lease_to_date = models.DateTimeField(default=datetime.now, blank=True)
    location = models.CharField(max_length=100, null=True)
    sublocality_level_1 = models.CharField(max_length=255, null=True)
    sublocality_level_2 = models.CharField(max_length=255, null=True)
    sublocality_level_3 = models.CharField(max_length=255, null=True)
    administrative_area_level_1 = models.CharField(max_length=255, null=True)
    administrative_area_level_2 = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    postal_code = models.IntegerField(default=0, null=True)
    latitude = models.CharField(max_length=255, null=True)
    longitude = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    status = models.CharField(max_length=50, choices=register_choices, default='requested')
    location_register_status = models.CharField(max_length=50, choices=location_register_choices,
                                                default='notregistered')
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'user_anchor'


class GroupWiseAncherLocationLabel(models.Model):
    labeltype_choices = (
        ('country', 'country'),
        ('state', 'state'),
        ('city', 'city'),
        ('locality', 'locality')
    )

    parent_id = models.IntegerField(default=0)
    label_type = models.CharField(max_length=50, choices=labeltype_choices, default='country')
    user_anchor_ids = JSONField(default=list, blank=True, null=True)
    user_anchor_latitudes = JSONField(default=list, blank=True, null=True)
    user_anchor_longitude = JSONField(default=list, blank=True, null=True)
    center_latitude = models.DecimalField(decimal_places=8, max_digits=1000, default=0.00)
    center_longitude = models.DecimalField(decimal_places=8, max_digits=1000, default=0.00)
    country = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)
    regiser_anchor_count = models.IntegerField(default=0, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'group_wise_ancher_location_label'


class CommendExecutionHistoryDetails(models.Model):
    hit_status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('success', 'success'),
        ('enqueue', 'enqueue')
    )
    point_status_choices = (
        ('insufficient point', 'insufficient point'),
        ('not detected', 'not detected'),
        ('failure', 'failure'),
        ('success', 'success')
    )
    query_execution_status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('close', 'close'),
        ('enqueue', 'enqueue')
    )
    aiori_query_execution_status_choices = (
        ('enqueue', 'enqueue'),
        ('terminated', 'terminated'),
        ('error', 'error'),
        ('success', 'success')
    )
    query_execution_interval_unit_choices = (
        ('second', 'second'),
        ('minute', 'minute'),
        ('hour', 'hour')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False},
                             related_name='history_details_user_id', null=True)
    commend_execution_history = models.ForeignKey(CommendExecutionHistory, on_delete=models.CASCADE,
                                                  limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                                  related_name='execution_id', null=True)
    users_host_group = models.ForeignKey(UsersHostGroup, on_delete=models.CASCADE,
                                         limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                         related_name='hostgroup_id', null=True)
    users_zone = models.ForeignKey(UsersZone, on_delete=models.CASCADE,
                                   limit_choices_to={'is_blocked': False, 'is_deleted': False}, related_name='zone_id',
                                   null=True)
    user_anchor = models.ForeignKey(UserAnchor, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='user_anchor_id', null=True)
    anchor_name = models.CharField(max_length=255, null=True, blank=True)
    host_id = models.IntegerField(default=0, null=True)
    host_name = models.CharField(max_length=255, null=True, blank=True)
    host_ip = models.CharField(max_length=255, null=True, blank=True)
    service_id = models.IntegerField(default=0, null=True)
    service_name = models.CharField(max_length=255, null=True, blank=True)
    service_domain_id = models.IntegerField(default=0, null=True)
    zone_id = models.IntegerField(default=0, null=True)
    zone_area_name = models.CharField(max_length=255, null=True, blank=True)
    anchor_id = models.IntegerField(default=0, null=True)
    dnsquery_type = models.CharField(max_length=255, null=True, blank=True)
    commend_query_id = models.CharField(max_length=255, null=True, blank=True)
    commend_request_payload = JSONField(default=dict)
    server_hit_status = models.CharField(max_length=100, choices=hit_status_choices, default='running')
    check_points_status = models.CharField(max_length=100, choices=point_status_choices, default='success')
    query_status = models.CharField(max_length=100, choices=query_execution_status_choices, default='enqueue')
    aiori_query_status = models.CharField(max_length=100, choices=aiori_query_execution_status_choices,
                                          default='enqueue')
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    query_execution_interval_unit = models.CharField(max_length=50, choices=query_execution_interval_unit_choices,
                                                     default='second')
    query_execution_interval_time = models.IntegerField(default=10, null=True)
    last_query_execution_data_sheen_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'commend_execution_history_details'


class RootServers(models.Model):
    server_name = models.CharField(max_length=255, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    server_ip_v4 = models.CharField(max_length=255, blank=True, null=True)
    server_ip_v6 = models.CharField(max_length=255, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'root_servers'


class AnchorHitRequest(models.Model):
    return_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('success', 'success')
    )
    hit_choices = (
        ('insufficient point', 'insufficient point'),
        ('not detected', 'not detected'),
        ('failure', 'failure'),
        ('success', 'success')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False},
                             related_name='request_user_id', null=True)
    hit_time = models.TimeField(default=timezone.now)
    schedule_time = models.TimeField(default=timezone.now)
    query_id = models.CharField(max_length=255, null=True, blank=True)
    request_payload = JSONField(default=dict)
    hit_status = models.CharField(max_length=50, choices=hit_choices, default='running')
    return_status = models.CharField(max_length=50, choices=return_choices, default='success')
    check_points_status = models.CharField(max_length=50, choices=return_choices, default='success')
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'anchor_hit_request'


class AnchorReturnDetails(models.Model):
    hit_return = models.ForeignKey(AnchorHitRequest, on_delete=models.CASCADE,
                                   limit_choices_to={'is_blocked': False, 'is_deleted': False}, related_name='hit_id',
                                   null=True)
    return_time = models.TimeField(blank=True)
    return_details = JSONField(default=dict)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'anchor_return_details'


class ServeIpDetails(models.Model):
    serve_location = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, default="", blank=True, null=True)
    country = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    postal = models.IntegerField(default=0, null=True)
    latitude = models.CharField(max_length=255, null=True)
    longitude = models.CharField(max_length=255, null=True)
    ip = models.CharField(max_length=255, null=True)
    org = models.CharField(max_length=255, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    request_counter = models.IntegerField(default=1, null=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'serve_ip_details'


class ServeMeasurementHistory(models.Model):
    status_choices = (
        ('running', 'running'),
        ('success', 'success')
    )

    serve_ip_details = models.ForeignKey(ServeIpDetails, on_delete=models.CASCADE,
                                         limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                         related_name='serve_ip_details_id', null=True)
    serve_measurement_id = models.CharField(max_length=255, null=True, blank=True)
    commend_request_payload = JSONField(default=dict)
    serve_location = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, default="", blank=True, null=True)
    country = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    postal = models.IntegerField(default=0, null=True)
    latitude = models.CharField(max_length=255, null=True)
    longitude = models.CharField(max_length=255, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    latency_status = models.CharField(max_length=50, choices=status_choices, default='running')
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'serve_measurement_history'


class ServeMeasurementHistoryDetails(models.Model):
    serve_measurement_history = models.ForeignKey(ServeMeasurementHistory, on_delete=models.CASCADE,
                                                  limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                                  related_name='serve_measurement_history_id', null=True)
    anchor = models.ForeignKey(Anchor, on_delete=models.CASCADE,
                               limit_choices_to={'is_blocked': False, 'is_deleted': False},
                               related_name='serve_anchor_id', null=True)
    commend_query_id = models.CharField(max_length=255, null=True, blank=True)
    commend_request_payload = JSONField(default=dict)
    vartual_anchor_location = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    rtt_avg = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_max = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_min = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    time = models.DateTimeField(default=timezone.now)
    protocol = models.CharField(max_length=100, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'serve_measurement_history_details'


class LatencyCheckHistory(models.Model):
    serve_ip_details = models.ForeignKey(ServeIpDetails, on_delete=models.CASCADE,
                                         limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                         related_name='latency_serve_ip_details_id', null=True)
    latency_measurement_id = models.CharField(max_length=255, null=True, blank=True)
    latency_check_domain_name = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    time = models.DateTimeField(default=timezone.now)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'latency_check_history'


class LatencyCheckHistoryDetails(models.Model):
    status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('success', 'success')
    )

    latency_check_history = models.ForeignKey(LatencyCheckHistory, on_delete=models.CASCADE,
                                              limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                              related_name='latency_check_history_id', null=True)
    anchor = models.ForeignKey(Anchor, on_delete=models.CASCADE,
                               limit_choices_to={'is_blocked': False, 'is_deleted': False},
                               related_name='aiori_anchor_id', null=True)
    user_anchor = models.ForeignKey(UserAnchor, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='register_anchor_id', null=True)
    anchor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='register_anchor_user_id', null=True)
    commend_request_payload = JSONField(default=dict)
    latency_check_domain_name = models.CharField(max_length=255, null=True, blank=True)
    register_anchor_location = models.CharField(max_length=255, null=True, blank=True)
    commend_query_id = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    rtt_avg = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_max = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_min = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    time = models.DateTimeField(default=timezone.now)
    execution_status = models.CharField(max_length=50, choices=status_choices, default='running')
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'latency_check_history_details'


class RootServerLatencyCheckHistoryDetails(models.Model):
    status_choices = (
        ('running', 'running'),
        ('failure', 'failure'),
        ('success', 'success')
    )

    root_server = models.ForeignKey(RootServers, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='root_server_id', null=True)
    anchor = models.ForeignKey(Anchor, on_delete=models.CASCADE,
                               limit_choices_to={'is_blocked': False, 'is_deleted': False},
                               related_name='root_server_latency_aiori_anchor_id', null=True)
    user_anchor = models.ForeignKey(UserAnchor, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='root_server_latency_register_anchor_id', null=True)
    anchor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                    related_name='root_server_latency_register_anchor_user_id', null=True)
    commend_request_payload = JSONField(default=dict)
    register_anchor_state = models.CharField(max_length=255, null=True, blank=True)
    register_anchor_location = models.CharField(max_length=255, null=True, blank=True)
    commend_query_id = models.CharField(max_length=255, null=True, blank=True)
    rtt_avg = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_max = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    rtt_min = models.DecimalField(decimal_places=3, max_digits=1000, default=0.00)
    soa_record = JSONField(default=dict)
    time = models.DateTimeField(default=timezone.now)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    execution_status = models.CharField(max_length=50, choices=status_choices, default='running')
    query_type = models.CharField(max_length=50, default='ping')
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'root_serverlatency_check_history_details'

class AnchorIpDetails(models.Model):

    STATUS_CHOICES = (
        ("online", "Online"),
        ("offline", "Offline"),
    )

    anchor_id = models.IntegerField(db_index=True, unique=True)

    anchor_name = models.CharField(max_length=512)

    user_anchor_id = models.IntegerField(db_index=True)

    ip_address = models.GenericIPAddressField()

    anchor_location = models.CharField(max_length=255)

    asn = models.CharField(max_length=10)

    isp = models.CharField(max_length=255)

    isp_location = models.CharField(max_length=255)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="online"
    )

    last_seen = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "anchors_ip_details"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["anchor_id"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        return f"Anchor-{self.anchor_id}"

class Measurement(models.Model):

    anchor_ip_id = models.ForeignKey(
        AnchorIpDetails,
        on_delete=models.CASCADE,
        related_name="measurements"
    )

    cluster_ip_id = models.ForeignKey(
        ClusterLocationNode,
        on_delete=models.CASCADE,
        related_name="measurements"
    )

    command_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    min_latency = models.FloatField(null=True, blank=True)
    avg_latency = models.FloatField(null=True, blank=True)
    max_latency = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    error_message = models.TextField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "measurements"
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["anchor_ip_id", "cluster_ip_id"]),
            models.Index(fields=["command_id"]),
        ]

    def __str__(self):
        return f"Measurement {self.id} | CMD {self.command_id}"
