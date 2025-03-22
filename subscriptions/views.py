from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import stripe
import json
from datetime import timedelta

from accounts.models import User
from .models import Subscription, PaymentHistory

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscribe(request, creator_username):
    """Handle subscription to a creator"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    if request.user == creator:
        messages.error(request, "You cannot subscribe to yourself.")
        return redirect('creator_profile', creator_username=creator_username)
    
    # Check if already subscribed
    if Subscription.objects.filter(subscriber=request.user, creator=creator, active=True).exists():
        messages.info(request, "You are already subscribed to this creator.")
        return redirect('creator_profile', creator_username=creator_username)
    
    try:
        # Create a payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(creator.subscription_price * 100),  # Convert to cents
            currency='usd',
            customer=request.user.stripe_customer_id,
            metadata={
                'creator_id': creator.id,
                'subscriber_id': request.user.id,
                'subscription_price': creator.subscription_price
            }
        )
        
        return render(request, 'subscriptions/subscribe.html', {
            'creator': creator,
            'client_secret': payment_intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY
        })
        
    except stripe.error.StripeError as e:
        messages.error(request, f"Stripe error: {str(e)}")
        return redirect('creator_profile', creator_username=creator_username)

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        creator_id = payment_intent['metadata']['creator_id']
        subscriber_id = payment_intent['metadata']['subscriber_id']
        
        try:
            subscriber = User.objects.get(id=subscriber_id)
            creator = User.objects.get(id=creator_id)
            
            # Set expiration date to 1 month from now
            expires_at = timezone.now() + timedelta(days=30)
            
            # Create the subscription
            subscription = Subscription.objects.create(
                subscriber=subscriber,
                creator=creator,
                active=True,
                created_at=timezone.now(),
                expires_at=expires_at,
                price=creator.subscription_price,
                auto_renew=True,
                stripe_payment_id=payment_intent['id']
            )
            
            # Record the payment
            PaymentHistory.objects.create(
                user=subscriber,
                recipient=creator,
                payment_type='subscription',
                amount=creator.subscription_price,
                status='succeeded',
                stripe_payment_id=payment_intent['id'],
                subscription=subscription
            )
            
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=200)

@login_required
def cancel_subscription(request, creator_username):
    """Handle subscription cancellation"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    try:
        subscription = Subscription.objects.get(
            subscriber=request.user,
            creator=creator,
            active=True
        )
        
        subscription.active = False
        subscription.auto_renew = False
        subscription.save()
        
        messages.success(request, "Your subscription has been cancelled.")
        
    except Subscription.DoesNotExist:
        messages.error(request, "No active subscription found.")
    
    return redirect('creator_profile', creator_username=creator_username)

@login_required
def subscription_confirmation(request, creator_username):
    """Display subscription confirmation page"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    # Get the most recent subscription
    subscription = Subscription.objects.filter(
        subscriber=request.user,
        creator=creator,
        active=True
    ).order_by('-created_at').first()
    
    if not subscription:
        messages.error(request, "No active subscription found.")
        return redirect('creator_profile', creator_username=creator_username)
    
    return render(request, 'subscriptions/subscription_confirmation.html', {
        'creator': creator,
        'subscription': subscription
    })
