from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/<str:username>/', views.subscribe_to_creator, name='subscribe'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('checkout/cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
] 