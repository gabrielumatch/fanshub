from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Subscription, PaymentHistory

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'creator', 'active', 'auto_renew', 'price', 'created_at', 'expires_at')
    list_filter = ('active', 'auto_renew', 'creator', 'created_at', 'expires_at')
    search_fields = ('subscriber__username', 'creator__username', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'expires_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('subscriber', 'creator', 'active', 'auto_renew', 'price')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        (_('Stripe Information'), {
            'fields': ('stripe_subscription_id',),
            'classes': ('collapse',),
            'description': 'Stripe-related information'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('subscriber', 'creator', 'price')
        return self.readonly_fields

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient', 'payment_type', 'amount', 'status', 'created_at')
    list_filter = ('payment_type', 'status', 'created_at')
    search_fields = ('user__username', 'recipient__username', 'stripe_payment_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'recipient', 'payment_type', 'amount', 'status')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        (_('Stripe Information'), {
            'fields': ('stripe_payment_id',),
            'classes': ('collapse',),
            'description': 'Stripe-related information'
        }),
        (_('Related Objects'), {
            'fields': ('subscription', 'post'),
            'classes': ('collapse',),
            'description': 'Related objects for this payment'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'recipient', 'payment_type', 'amount')
        return self.readonly_fields
