from django.urls import path
from . import views

app_name = 'services_app'

urlpatterns = [
    #path('', views.index, name='index'),
    path('login/', views.index, name='index'),
    path('', views.dashboard, name='dashboard'),
    #path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('get_registration/', views.get_registration, name='get_registration'),
    path('users/login/', views.user_login, name='user_login'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password-generation/', views.forgot_password_generation, name='forgot_password_generation'),
    path('send-reset-link-to-student/', views.faculty_reset_student_password, name='faculty_reset_student_password'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_img'),
    path('change-profile-password/', views.change_profile_password, name='change_profile_password'),
    # Discussion routes removed (feature disabled)
    path('domain/', views.DomainView.as_view(), name='domain'),
    path('zone/', views.ZoneView.as_view(), name='zone'),
    # Anchor registration feature removed (safe, non-destructive)
    path('anchor/', views.anchor_removed, name='anchor'),
    path('anchor-register-page/', views.anchor_removed, name='anchor_register_page'),
    path('user-anchor-registration/', views.user_anchor_registration_removed, name='user_anchor_registration'),
    path('user-anchor-update-location/', views.user_anchor_update_location_removed, name='user_anchor_update_location'),
    path('ping-command/', views.ping_command_page, name='ping_command_page'),
    path('generate-ping-query/', views.generate_ping_query, name='generate_ping_query'),

    path('ping_visualizer/', views.ping_visualizer, name='ping_visualizer'),

    path('linked-queries-dashboard/', views.linked_queries_by_student_dashboard, name='linked_queries_by_student_dashboard'),
    # (duplicate discussion routes removed)

    path('assignment/', views.AssignmentView.as_view(), name='assignment'),
    path('link-query/',views.query_linking_by_student, name='link_query'),
    path('edit-linked-query/',views.editing_linkedquery_by_student, name='editing_linkedquery_by_student'),
    path('associated-measurement-logs/', views.associated_measurement_logs, name='associated_measurement_logs'),
    path('enroll-students/', views.enroll_students, name='enroll_students'),

    path('create-student/', views.create_student, name='create_student'),
    path('delete-student/', views.delete_student, name='delete_student'),
    path('student-details-by-mail/', views.student_details_fetch_by_mail, name='student_details_fetch_by_mail'),
    path('student-point-details-by-userid/', views.student_point_details_fetch_by_userid, name='student_point_details_fetch_by_userid'),
    path('linked-queries/', views.student_linked_queries_by_userid, name='student_linked_queries_by_userid'),
    path('recharge-points-student/', views.recharge_points_students, name='recharge_points_students'),


    path('user-list/', views.user_list, name='user_list'),
    path('user-list-point-details/', views.user_list_point_details, name='user_list_point_details'),
    path('user-report/', views.user_report, name='user_report'),
    path('admin-point-add/', views.point_addition_admin, name='admin_point_add'),
    path('anchor-list/', views.anchor_removed, name='admin_anchor_list'),
    # delete and block user by admin
    # path('user-delete/', views.delete_user_by_admin, name='delete_user'),
    # path('user-block/', views.block_user_by_admin, name='block_user'),
    # path("filter-user-data/", views.public_filter_user_data, name="filter-user-data"),
    path('engagement_opportunity/', views.engagement_opportunity, name='engagement_opportunity'),
    path('public-measurements/', views.public_measurement, name='public_measurement'),
    path('public-report/', views.public_report, name='public_report'),
    path('qr-codes/', views.qr_code_list_view, name='qr_code_list_view'),
    path('admin-faculty-student-list/', views.admin_faculty_student_list, name='admin_faculty_student_list'),
    path('faculty-student-list/', views.faculty_student_list, name='faculty_student_list'),

    path('export-user-report/', views.export_user_report, name='export_user_report'),
]
