from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('subscribe/<str:creator_username>/', views.subscribe, name='subscribe'),
    path('cancel/<str:creator_username>/', views.cancel_subscription, name='cancel_subscription'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('confirmation/<str:creator_username>/', views.subscription_confirmation, name='subscription_confirmation'),
] 