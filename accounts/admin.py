from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin to show UserProfile within User admin page
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom User admin that includes the profile inline
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model
    """
    list_display = ('user', 'phone_number', 'city', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'city')
    list_filter = ('city', 'country', 'created_at')
    ordering = ('-created_at',)