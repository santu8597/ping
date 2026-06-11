from django.urls import path, re_path
from .views import StudentCreationView, FacultyStudentListView, \
    StudentProfileView, AssignmentListCreateView, LinkedAssignmentListCreateView, AssignmentDetailView, \
    LinkedAssignmentDetailView, StudentAssignmentListView, StudentPointUtilizationView, AssignmentLinkedQueriesView, \
    RechargePointsView, StudentAssignmentsView, UploadProfileImageView, ForgotPasswordView, ResetPasswordView, \
    EmailVerificationCheckView, UserStatsAPIView, FacultyStudentAPIView
from backend.users.webservice import signin_signup_view, discussion_forum_view, user_domain_view, host_query_management_view, profile_view
from django.conf import settings
from django.conf.urls.static import static

from .webservice.signin_signup_view import UserSessionView

app_name = 'users'

urlpatterns = [

    path('faculty/students/', FacultyStudentListView.as_view(), name='student-create'),
    path('student/create/', StudentCreationView.as_view(), name='student-create'),
    path('student/profile/', StudentProfileView.as_view()),

    # User Registration

    path('registration/', signin_signup_view.UserRegistrationView.as_view(), name='registration'),


    path('session/', UserSessionView.as_view(), name='user-session'),
    path('user-login/', signin_signup_view.UserLoginView.as_view(), name='user-login'),
    path('email/verify/', EmailVerificationCheckView.as_view(), name='verify-email'),


    path('forgot/password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('user/reset-password-form/', ResetPasswordView.as_view(), name='reset-password-form'),

    path('change-password/', signin_signup_view.UserChangePasswordView.as_view(), name='change-password'),
    path('profile-details/', profile_view.ProfileDeatailView.as_view(), name='profile-details'),
    path('upload/profile-image/', UploadProfileImageView.as_view(), name='upload-profile-image'),

    # User Discussion Forum Management #
    #re_path(r'^discussions/(?P<topicid>\w{0,10})/$', discussion_forum_view.DiscussionView.as_view(), name='discussions'),
        # Discussion forum API routes removed (feature disabled)
    
    # User Domain Management #
    path('user-domain/', user_domain_view.DomainView.as_view(), name='user-domain'),
    path('domain-details/', user_domain_view.DomainDetailsView.as_view(), name='domain-details'),

    # User Zone Management #
    path('user-zone/', host_query_management_view.ZoneView.as_view(), name='user-zone'),
    path('user-zone-details/', host_query_management_view.ZoneDetailsView.as_view(), name='user-zone-details'),

    # User Host Management #
    path('user-host-group/', host_query_management_view.HostGroupView.as_view(), name='user-host-group'),
    path('user-host-group-details/', host_query_management_view.HostGroupDetailsView.as_view(), name='user-host-group-details'),


    # Admin Login #
    path('user-list/', signin_signup_view.UserListView.as_view(), name='user-list'),

    # Admin can Login To user #
    path('admin-user-login/', signin_signup_view.AdminUserLogin.as_view(), name='admin-user-login'),

    # User Report Api #
    path('user-report-profile-det/', profile_view.UserReportProfileView.as_view(), name='user-report-profile-det'),
    path('user-report-domain-det/', user_domain_view.UserReportDomainView.as_view(), name='user-report-domain-det'),
    path('user-report-zone-det/', host_query_management_view.UserReportZoneView.as_view(), name='user-report-zone-det'),
    path('user-report-host-group-det/', host_query_management_view.UserReportHostGroupView.as_view(), name='user-report-host-group-det'),

    # Teacher assignment CRUD
    path('faculty/assignments/', AssignmentListCreateView.as_view(), name='assignment-list-create'),
    path('faculty/assignments/<int:id>/', AssignmentDetailView.as_view(), name='assignment-detail'),
    path('faculty/student/<int:student_id>/assignments/', StudentAssignmentListView.as_view(), name='student-assignment'),
    path('student/view/assignments/', StudentAssignmentsView.as_view(), name='student-assignments'),
    path('assignments/<int:assignment_id>/linked-queries/', AssignmentLinkedQueriesView.as_view(), name='assignment-linked-queries'),

    # Faculty sees point-utilization
    path('student/<int:student_id>/point-utilization/', StudentPointUtilizationView.as_view(), name='student-point-utilization'),
    path('recharge/', RechargePointsView.as_view(), name='recharge-points'),


    # Student linked assignment
    path('student/assignments/', LinkedAssignmentListCreateView.as_view(), name='linked-assignment-list-create'),
    path('student/assignments/<int:id>/', LinkedAssignmentDetailView.as_view(), name='linked-assignment-detail'),

    path('user-stats/', UserStatsAPIView.as_view(), name='user-stats'),
    path('faculty-students/', FacultyStudentAPIView.as_view(), name='faculty-students'),



]
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)