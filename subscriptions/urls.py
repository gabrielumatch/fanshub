from django.urls import path
from .views.subscriptions import (
    subscribe,
    cancel_subscription,
    subscription_confirmation,
    stripe_webhook,
    check_subscription
)
from .views.payment_methods import (
    list_payment_methods,
    save_payment_method,
    set_default_payment_method,
    delete_payment_method
)

app_name = 'subscriptions'

urlpatterns = [
    path('subscribe/<str:creator_username>/', subscribe, name='subscribe'),
    path('cancel/<str:creator_username>/', cancel_subscription, name='cancel_subscription'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    path('confirmation/<str:creator_username>/', subscription_confirmation, name='subscription_confirmation'),
    path('payment-methods/', list_payment_methods, name='list_payment_methods'),
    path('payment-methods/save/', save_payment_method, name='save_payment_method'),
    path('payment-methods/set-default/', set_default_payment_method, name='set_default_payment_method'),
    path('payment-methods/delete/', delete_payment_method, name='delete_payment_method'),
    path('api/subscriptions/check/<str:subscription_id>/', check_subscription, name='check_subscription'),
] 