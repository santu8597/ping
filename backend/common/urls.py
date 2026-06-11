from django.urls import path

from .views import SendOTPView, ValidateOTPView, SendMobileOTPView, VerifyMobileOTPView, ResendOTP
from .webservice import common_view, blog_view, rootviz,cluster_data
from django.conf import settings
from django.conf.urls.static import static

app_name = 'common'


urlpatterns = [

    #path('', views.IndexView.as_view(), name='index'),
    path('country-list/', common_view.CountryListView.as_view(), name='country-list'),
    path('state-list/', common_view.StateListView.as_view(), name='state-list'),
    path('city-list/', common_view.CityListView.as_view(), name='city-list'),

    path('features/', common_view.HighlightedFeaturesView.as_view(), name='features'),
    path('user-menus/', common_view.UserMenuListView.as_view(), name='user-menus'),

    # # FOR ADMIN LOGIN #
    path('menu-master/', common_view.MenuMasterListView.as_view(), name='menu-master'),

    # # LOADING MENU OPTION
    path('user-group/', common_view.UserGroupListView.as_view(), name='user-group'),
    path('menu-list-by-parent/', common_view.MenuByParentListView.as_view(), name='menu-list-by-parent'),
    path('menu-by-id/', common_view.MenuByIdListView.as_view(), name='menu-by-id'),

    path('user-menu-by-role/', common_view.MenuByUserGroupView.as_view(), name='user-menu-by-role'),
    path('user-list-by-role/', common_view.UserListByGroupView.as_view(), name='user-list-by-role'),
    path('user-list-wethout-role/', common_view.UserListWethoutGroupView.as_view(), name='user-list-wethout-role'),

    path('user-group-management/', common_view.UserGroupManagmentView.as_view(), name='user-group-management'),

    # Layout  Management #

    path('research-layout/', common_view.ResearchPageLayoutView.as_view(), name='research-layout'),

    #User Anchor  Management #

    path('anchor-locations/', common_view.AnchorLocationView.as_view(), name='anchor-locations'),
    path('unicast-anchor-locations/', common_view.UnicastAnchorLocationView.as_view(), name='unicast-anchor-locations'),

    # User Blog  Management #
    path('post-blog/', common_view.BlogPostView.as_view(), name='post-blog'),
    path('blogs/', common_view.BlogView.as_view(), name='blogs'),
    path('blog-image/', blog_view.BlogFileUploadView.as_view(), name='blog-image'),

    # Default Settings  Management #

    path('default-settings/', common_view.SiteSettingsView.as_view(), name='default-settings'),
    path('settings-details/', common_view.SiteSettingsDetailsView.as_view(), name='settings-details'),


    path('otp/send/', SendOTPView.as_view(), name='send-otp'),
    path('otp/validate/', ValidateOTPView.as_view(), name='validate-otp'),

    path('mobile/otp/send/', SendMobileOTPView.as_view(), name='send-mobile-otp'),
    path('mobile/otp/validate/', VerifyMobileOTPView.as_view(), name='validate-mobile-otp'),

    path('otp/resend/', ResendOTP.as_view(), name='resend_otp'),


    # ROOT Viz from Root Server
    # path('root-viz/<str:filename>', rootviz.RootvizProxyAPIView.as_view(), name='root-viz'),
    path("root-data/", rootviz.RootvizDailyAPIView.as_view()),
    path("cluster-locations/",cluster_data.ClusterLocationsAPIView.as_view(), name="cluster-locations"),
    path("cluster-locations/<int:pk>/", cluster_data.ClusterLocationsAPIView.as_view()),
]
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)