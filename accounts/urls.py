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
    path('technician_directory/', views.technician_directory_view, name='technician_directory'),
    path('user_message/', views.user_messages_view, name='user_message'),
    path('debug/storage-detailed/', views.debug_storage_detailed, name='debug_storage_detailed'),
    path('debug/comprehensive-test/', views.comprehensive_storage_test, name='comprehensive_test'),
    path('debug/current-picture/', views.debug_current_profile_picture, name='debug_current_picture'),
    path('debug/storage-config/', views.debug_storage_config, name='debug_storage_config'),
    path('debug/direct-connection/', views.test_direct_supabase_connection, name='direct_connection'),
    path('debug/list-files/', views.list_bucket_files, name='list_files'),
    path('debug/upload-flow/', views.debug_upload_flow, name='debug_upload_flow'),
    path('debug/storage-type/', views.check_current_storage, name='check_storage_type'),
    path('technician/<int:technician_id>/', views.technician_detail_view, name='technician_detail'),
    path('request-assistance/', views.request_assistance_view, name='request_assistance'),
    path('request-assistance/assign/', views.assign_ticket_to_technician, name='assign_ticket_to_technician'),
    path('technician/<int:technician_id>/availability/', views.get_technician_availability, name='technician_availability'),
    path('technician-messages/', views.technician_messages_view, name='technician_messages'),
    path('technician-tickets/', views.technician_tickets_view, name='technician_tickets'),
    path('technician/ticket/<int:ticket_id>/resolve/', views.resolve_ticket, name='resolve_ticket'),
    path('technician/ticket/<int:ticket_id>/start-work/', views.start_work_ticket, name='start_work_ticket'),
    path('debug-request/', views.debug_request_assistance, name='debug_request'),
    path('api/delete-message/', views.handle_delete_message, name='delete_message'),
    path('user/chat/delete/', views.handle_delete_chat, name='user_delete_chat'),
    path('technician/chat/delete/', views.handle_delete_chat, name='technician_delete_chat'),
    path('api/chat/<int:chat_session_id>/messages/', views.get_chat_messages, name='get_chat_messages'),
    path('api/messages/unread-count/', views.get_unread_count, name='get_unread_count'),
    path('technician/debug/fix-chats/', views.debug_fix_chats, name='debug_fix_chats'),
    # path('technician/debug/data/', views.debug_technician_data, name='debug_technician_data'),
    #FAQ/Help Center
    path('help-center/', views.help_center_view, name='help_center'),
    path('faq/', views.help_center_view, name='faq'),
    path('help/api/faq/<int:faq_id>/', views.get_faq_detail, name='get_faq_detail'),
    path('help/api/category/<slug:category_slug>/', views.get_category_faqs, name='get_category_faqs'),
    
    #History
    path('profile/history/', views.ticket_history, name='ticket_history'),
    path('technician/debug/data/', views.debug_technician_data, name='debug_technician_data'),


    #Settings
    path('settings/', views.settings_view, name='settings'),
    path('technician-settings/', views.technician_settings_view, name='technician_settings'),
    path('user-settings/', views.user_settings_view, name='user_settings'),
    path('settings/update/', views.update_notifications, name='update_notifications'),
    path('settings/change-password/', views.change_password_settings, name='change_password'),
    path('account/delete/', views.delete_account_view, name='delete_account'),

    #CREATING TICKET
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),  #VIEW
path('available-technicians/', views.available_technicians, name='available-technicians'),
    
    path('ticket/<int:ticket_id>/', views.ticket_details_view, name='ticket_details'),
    path('ticket/<int:ticket_id>/review/', views.submit_ticket_review, name='submit_ticket_review'),
    path('technician/ticket/<int:ticket_id>/', views.technician_ticket_details_view, name='technician_ticket_details'),

    #DELETE TICKET
path('ticket/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),


]
