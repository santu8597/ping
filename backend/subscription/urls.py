from django.urls import path
from backend.subscription.webservice import subscription_view

app_name = 'subscription'

urlpatterns = [
    path('plans/', subscription_view.SubscriptionView.as_view(), name='plans'),
    # User Signin Signup  Management #
    path('user-subscription/', subscription_view.UserSubscriptionView.as_view(), name='user-subscription'),
    path('point-utilization/', subscription_view.PointUtilizationView.as_view(), name='point-utilization'),
    path('user-point/', subscription_view.UserPointView.as_view(), name='user-point'),
    
    # User Report Api #
    path('user-report-plans/', subscription_view.UserReportSubscriptionView.as_view(), name='user-report-plans'),
    path('user-report-points-spend/', subscription_view.UserReportPointsUsedView.as_view(), name='user-report-points-spend'),

    path('export-user-report/', subscription_view.ExportUserExecutionCSV.as_view(), name='export-user-report')]