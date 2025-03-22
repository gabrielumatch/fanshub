from django.contrib import admin
from .models import Subscription, PaymentHistory

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'creator', 'active', 'price', 'created_at', 'expires_at')
    list_filter = ('active', 'creator')
    search_fields = ('subscriber__username', 'creator__username')

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient', 'payment_type', 'amount', 'status', 'created_at')
    list_filter = ('payment_type', 'status')
    search_fields = ('user__username', 'recipient__username')
