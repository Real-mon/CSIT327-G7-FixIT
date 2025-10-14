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
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('change-password/', views.change_password_view, name='change_password'),  # ADD THIS
    path('technician-dashboard/', views.technician_dashboard_view, name='technician_dashboard'),
    path('user-dashboard/', views.user_dashboard_view, name='user_dashboard'),
]