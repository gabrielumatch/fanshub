from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User
from subscriptions.models import Subscription

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'creator'
    readonly_fields = ('subscriber', 'active', 'price', 'created_at', 'expires_at', 'auto_renew')
    can_delete = False
    max_num = 0
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_creator', 'is_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_creator', 'is_verified', 'is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'bio')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'bio', 'profile_picture', 'cover_photo', 'date_of_birth')}),
        (_('Creator Settings'), {
            'fields': ('is_creator', 'subscription_price', 'stripe_account_id', 'stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',),
            'description': 'Settings specific to creator accounts'
        }),
        (_('Verification'), {
            'fields': ('verification_document', 'is_verified'),
            'classes': ('collapse',),
            'description': 'Creator verification settings'
        }),
        (_('Payment Info'), {
            'fields': ('stripe_customer_id',),
            'classes': ('collapse',),
            'description': 'Payment-related information'
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_creator'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('username',)
        return self.readonly_fields
    
    def get_inlines(self, request, obj=None):
        if obj and obj.is_creator:
            return [SubscriptionInline]
        return []
