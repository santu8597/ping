# from django.conf.urls import url, include     # Old one
from django.urls import path, re_path
from . import webservice
from rest_framework.authtoken import views as restview
from apscheduler.schedulers.background import BackgroundScheduler
import pytz  # New Addition

from datetime import datetime
# from apscheduler.schedulers.blocking import BlockingScheduler
from django.conf import settings
from django.conf.urls.static import static
# from apscheduler.scheduler import Scheduler
from .sync import sync_anchor_ip, sync_pending_measurements
from .webservice import command_name_view, commend_execution_view, influxdb_client, download_view, \
    anchor_registration_view, anycast_view,qr_api_view


from .views import QueryStatsAPIView

app_name = 'anchor'

urlpatterns = [
    ##### Anchor  Management #####
    path('command-name/', command_name_view.Command_Name_View.as_view(), name='command-name-list'),
    path('block-command/', command_name_view.Block_Command_View.as_view(), name='block-command'),
    path('run-command/', command_name_view.Run_Command_View.as_view(), name='run-command'),
    path('command-history/', commend_execution_view.CommandHistoryView.as_view(), name='command-history'),
    #re_path(r'^command-history-details-by_id/(?P<historyid>\w{0,10})/$', commend_execution_view.CommandHistoryDetailsView.as_view(), name='command-history-details-by_id'),
    re_path(r'^command-history-details-by_id/(?P<historyid>\d+)/?$', commend_execution_view.CommandHistoryDetailsView.as_view(), name='command-history-details-by_id'),


    path('command-history-details-by_id/', commend_execution_view.CommandHistoryDetailsView.as_view(), name='command-history-details-by_id'),

    path('group-command-history/', commend_execution_view.GroupCommandHistoryView.as_view(), name='group-command-history'),
    path('preiodic-command-history-with-anchor-or-zone/', commend_execution_view.PeriodicCommandHistoryWithZoneOrAnchorView.as_view(), name='preiodic-command-history-with-anchor-or-zone'),

    path('command-history-details/', commend_execution_view.GroupCommandHistoryDetailsView.as_view(), name='command-history-details'),
    path('command-result/', influxdb_client.CommandResultView.as_view(), name='command-result'),
    path('command-result-by-id/', influxdb_client.CommandResultByHistoryIdView.as_view(), name='command-result-by-id'),
    path('regular-zone-command-result/', influxdb_client.RegularZoneCommandResultView.as_view(), name='regular-zone-command-result'),

    path('periodic-command-result/', influxdb_client.PeriodicCommandResultView.as_view(), name='periodic-command-result'),
    path('periodic-result/', influxdb_client.PeriodicResultView.as_view(), name='periodic-result'),

    path('periodic-result-by-id/', influxdb_client.PeriodicResultByIdView.as_view(), name='periodic-result-by-id'),
    path('periodic-groupby-result/', influxdb_client.PeriodicGroupByResultView.as_view(), name='periodic-groupby-result'),
    path('zone-periodic-result/', influxdb_client.ZonePeriodicResultView.as_view(), name='zone-periodic-result'),
    path('periodic-zone-groupby-result/', influxdb_client.PeriodicZoneGroupByResultView.as_view(), name='periodic-zone-groupby-result'),

    path('anchor-request/', anchor_registration_view.AnchorView.as_view(), name='anchor-request'),
    path('user-anchor/', anchor_registration_view.UserAnchorView.as_view(), name='user-anchor'),
    path('user-qr-code/', anchor_registration_view.UserQrCodeView.as_view(), name='user-qr-code'),
    path('anchor-register/', anchor_registration_view.RegisterAnchorView.as_view(), name='anchor-register'),
    path('anchor-register-by-name/', anchor_registration_view.LeaseAnchorByAnchorNameView.as_view(), name='anchor-register-by-name'),
    path('anchor-details/', anchor_registration_view.RegisterAnchorDetailsView.as_view(), name='anchor-details'),

    path('register-anchor-by-location/', anchor_registration_view.LocationWiseUserAnchorView.as_view(), name='register-anchor-by-location'),
    path('anchor-map-coordinates/', anchor_registration_view.AnchorMapCoordinatesView.as_view(), name='anchor-map-coordinates'),

    ##### Anchor Data Download Management #####
    # re_path(r'^downloads/(?P<pk>\d+)/$', download_view.ExportAsCSV.as_view(), name='downloads'),
    re_path(r'^downloads/(?P<pk>\d+)/?$', download_view.ExportAsCSV.as_view(), name='downloads'),


    ####### Anycast OR Outside Any Side Call API Services Management ######
    path('anchor-measurement/', anycast_view.LocationWiseMeasurementView.as_view(), name='anchor-measurement'),
    path('serve-measurement/', anycast_view.MeasurementServeView.as_view(), name='serve-measurement'),
    # re_path(r'^serve-measurement/(?P<measurementid>\w{0,50})/$', anycast_view.MeasurementServeView.as_view(), name='serve-measurement'),
    re_path(r'^serve-measurement/(?P<measurementid>[A-Za-z0-9]+)/?$', anycast_view.MeasurementServeView.as_view(), name='serve-measurement'),

    #re_path(r'^city-latency/(?P<city>.+)/$', anycast_view.ServeLatencyByCityView.as_view(), name='city-latency'),
    re_path(r'^city-latency/(?P<city>[A-Za-z0-9]+)/?$', anycast_view.ServeLatencyByCityView.as_view(), name='city-latency'),

    #re_path(r'^check-latency/(?P<latencyid>\w{0,10})/$', anycast_view.LatencyCheckAllAnchorView.as_view(), name='check-latency'),
    re_path(r'^check-latency/(?P<latencyid>[A-Za-z0-9]+)/?$', anycast_view.LatencyCheckAllAnchorView.as_view(), name='check-latency'),

    path('check-latency/', anycast_view.LatencyCheckAllAnchorView.as_view(), name='check-latency'),
    # re_path(r'^sunbust-check-latency/(?P<latencyid>\w{0,10})/$', anycast_view.SunbustFormatLatencyCheckAllAnchorView.as_view(), name='sunbust-check-latency'),
    re_path(r'^sunbust-check-latency/(?P<latencyid>\d+)/?$', anycast_view.SunbustFormatLatencyCheckAllAnchorView.as_view(), name='sunbust-check-latency'),


    path('serve-location-linechart-data/', anycast_view.MeasurementServeDetailsView.as_view(), name='serve-location-linechart-data'),
    path('serve-location-piechart-data/', anycast_view.MeasurementServeDetailsPieView.as_view(), name='serve-location-piechart-data'),
    path('serve-map-coordinate/', anycast_view.ServeMapView.as_view(), name='serve-map-coordinate'),
    path('serve-research/', anycast_view.ServeResearchView.as_view(), name='serve-research'),
    path('all-city-latency/', anycast_view.ServeLatencyAllCityView.as_view(), name='all-city-latency'),
    path('latency-check-graph-view/', anycast_view.ServeLatencyCheckView.as_view(), name='latency-check-graph-view'),
    path('routing-detore-view/', anycast_view.ServeRoutingDetoreView.as_view(), name='routing-detore-view'),
    path('telephone-circle-routing-detore/', anycast_view.TelephoneCircleRoutingDetoreView.as_view(), name='telephone-circle-routing-detore'),
    path('telephone-circle-serve-location-routing-detore/', anycast_view.TelephoneCircleServeLocationRoutingDetoreView.as_view(), name='telephone-circle-serve-location-routing-detore'),
    path('asn-routing-detore/', anycast_view.AsnWiseDetourServeLocationView.as_view(), name='asn-routing-detore'),
    path('anycast-server-list/', anycast_view.AnycastServerLocationView.as_view(), name='anycast-server-list'),
    path('root-server-list/', anycast_view.RootServerListView.as_view(), name='root-server-list'),
    path('root-server-states-locations/', anycast_view.RootServerStatesAndLocationsView.as_view(), name='root-server-states-locations'),
    path('root-server-state-wise-latency/', anycast_view.RootServerStateWiseLatencyView.as_view(), name='root-server-state-wise-latency'),
    path('root-server-soa-record/', anycast_view.RootServerSoaRecordsView.as_view(), name='root-server-sos-record'),
# QR Code API View
    path('qr-codes/', qr_api_view.QrCodeListAPIView.as_view(), name='qr_code_api'),

    path('anchor-update/', anchor_registration_view.AnchorUpdate.as_view(), name='anchor-update'),
    path('anchor-ip-details-update/', anchor_registration_view.AnchorIpDetailsUpdate.as_view(), name='anchor-ip-details-update'),
    path('anchor-network/', anchor_registration_view.ActiveAnchorNetworkView.as_view(), name='anchor-network'),
    path('aiori-anchor-query-execution-request/', commend_execution_view.RD3MNCommandExecutionView.as_view(), name='aiori-anchor-query-execution-request'),
    path('root-server/', anycast_view.RootServerView.as_view(), name='root-server'),
    path('root-server-pin-result/', anycast_view.RootServerPinResultUpdateView.as_view(), name='root-server-pin-result'),
    path('root-server-soa-result/', anycast_view.RootServerSoaResultUpdateView.as_view(), name='root-server-soa-result'),

    # re_path(r'^root-server-state-wise-latency-download/(?P<form_date>.+)/(?P<to_date>.+)/(?P<rootserver_name>.+)/$', anycast_view.RootServerStateWiseLatencyDownloadView.as_view(), name='root-server-state-wise-latency-download'),
    re_path(r'^root-server-state-wise-latency-download/(?P<form_date>\d{4}-\d{2}-\d{2})/(?P<to_date>\d{4}-\d{2}-\d{2})/(?P<rootserver_name>[^/]+)/$',anycast_view.RootServerStateWiseLatencyDownloadView.as_view(),name='root-server-state-wise-latency-download'),
    path('execution-history/', commend_execution_view.CommendExecutionHistoryListAPIView.as_view(), name='execution-history-list'),
    path('query-stats/', QueryStatsAPIView.as_view(), name='query-stats'),
    path('active-anchor-zone-count/', anchor_registration_view.ActiveAnchorZoneCountView.as_view(), name='active-anchor-zone-count'),
    path('registered-anchor-zone-count/', anchor_registration_view.RegisteredAnchorZoneCountView.as_view(), name='registered-anchor-zone-count'),

    # Measurement
    path('measurements/', anycast_view.MeasurementListResource.as_view(), name='measurements-list'),
    re_path(r'^measurements/(?P<id>\d+)/?$', anycast_view.MeasurementResource.as_view(), name='measurements'),
    re_path(r'^measurements/cluster/(?P<cluster_ip>\d+)/?$', anycast_view.MeasurementByClusterIPResource.as_view(), name='measurements-by-cluster-ip'),
    re_path(r'^measurements/cluster/(?P<cluster_id>\d+)/anchor/(?P<anchor_ip_id>\d+)/?$',anycast_view.MeasurementByIPIDDetailsResource.as_view(),name='measurements-by-cluster-anchor'),

]
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ----------------------------------------------------------------
#
#   Application Scheduler // pip install apscheduler.
#
# ----------------------------------------------------------------
import threading

# scheduler = BackgroundScheduler()     # Old one
scheduler = BackgroundScheduler(timezone=pytz.timezone('UTC'))
# scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))

scheduler.add_job(commend_execution_view.QueryHistoryStatusUpdateCorn, 'interval', minutes=30)
scheduler.add_job(anchor_registration_view.SaveAnchorDetailsFromAIORICronClass, 'interval', minutes=53)
# scheduler.add_job(anchor_registration_view.UserLeaseAnchorResetCron, 'interval', minutes=1440)
scheduler.add_job(
    sync_anchor_ip,
    'cron',
    day_of_week='sat',
    hour=2,
    minute=0,
    id='sync_anchor_ip_weekly',
    replace_existing=True
)

scheduler.add_job(
    sync_pending_measurements,
    'cron',
    hour=17,
    minute=0,
    id='sync_pending_measurements_daily',
    replace_existing=True
)
scheduler.add_job(commend_execution_view.RD3MNPinCommandExecutionCornView, 'interval', minutes=7)
scheduler.add_job(anycast_view.RD3MNPinCommandExecutionForRootServerCornView, 'cron', hour=0, minute=30)
scheduler.add_job(anycast_view.RootServerPinResultUpdateCornView, 'cron', hour=0, minute=40)
# scheduler.add_job(anycast_view.RootServerSoaResultUpdateCornView, 'interval', hours=15, minutes=20)
scheduler.start()
# scheduler.add_job(commend_execution_view.printit, 'cron', second=1)

