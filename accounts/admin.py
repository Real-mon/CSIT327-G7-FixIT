from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile
from django.contrib import admin
from .models import FAQCategory, FAQItem


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
    
@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'faq_count', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'icon']
    
    def faq_count(self, obj):
        return obj.faqs.count()
    faq_count.short_description = 'FAQ Items'


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ['short_question', 'category', 'order', 'is_active', 'bot_priority', 
                    'show_in_dashboard', 'show_in_bot_buttons', 'read_time']
    list_filter = ['category', 'is_active', 'show_in_dashboard', 'show_in_bot_buttons']
    search_fields = ['question', 'short_question', 'answer', 'keywords']
    list_editable = ['order', 'is_active', 'bot_priority', 'show_in_dashboard', 
                     'show_in_bot_buttons', 'read_time']
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'question', 'short_question', 'answer', 'short_answer')
        }),
        ('Bot Settings', {
            'fields': ('keywords', 'bot_priority', 'show_in_bot_buttons')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active', 'show_in_dashboard', 'read_time')
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/faq_admin.css',)
        }