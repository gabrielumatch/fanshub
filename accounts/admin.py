from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_creator', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_creator', 'is_staff', 'is_active', 'groups')
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
