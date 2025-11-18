from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('role-select/', views.role_select_view, name='role_select'),
    path('profile/user/', views.user_profile_view, name='user_profile'),
    path('profile/technician/', views.technician_profile_view, name='technician_profile'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('change-password/', views.change_password_view, name='change_password'),  # ADD THIS
    path('technician-dashboard/', views.technician_dashboard_view, name='technician_dashboard'),
    path('user-dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('user_message/', views.user_messages_view, name='user_message'),
    path('debug/storage-detailed/', views.debug_storage_detailed, name='debug_storage_detailed'),
    path('debug/comprehensive-test/', views.comprehensive_storage_test, name='comprehensive_test'),
    path('debug/current-picture/', views.debug_current_profile_picture, name='debug_current_picture'),
    path('debug/storage-config/', views.debug_storage_config, name='debug_storage_config'),
    path('debug/direct-connection/', views.test_direct_supabase_connection, name='direct_connection'),
    path('debug/list-files/', views.list_bucket_files, name='list_files'),
    path('debug/upload-flow/', views.debug_upload_flow, name='debug_upload_flow'),
    path('debug/storage-type/', views.check_current_storage, name='check_storage_type'),
     

     

    #History
    path('profile/history/', views.ticket_history, name='ticket_history'),


    #Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/update/', views.update_notifications, name='update_notifications'),
    path('settings/change-password/', views.change_password_settings, name='change_password'),

    #CREATING TICKET
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),  #VIEW
path('available-technicians/', views.available_technicians, name='available-technicians'),
]