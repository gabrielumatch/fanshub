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
def subscribe_to_creator(request, username):
    """Handle subscription to a creator"""
    creator = get_object_or_404(User, username=username, is_creator=True)
    
    # Check if user is already subscribed
    existing_subscription = Subscription.objects.filter(
        subscriber=request.user,
        creator=creator,
        active=True
    ).first()
    
    if existing_subscription:
        messages.info(request, _('You are already subscribed to this creator.'))
        return redirect('creator_profile', username=username)
    
    # Create a Stripe checkout session
    try:
        success_url = request.build_absolute_uri(reverse('checkout_success'))
        cancel_url = request.build_absolute_uri(reverse('checkout_cancel'))
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Subscription to {creator.username}',
                            'description': f'1 month access to {creator.username}\'s exclusive content',
                        },
                        'unit_amount': int(creator.subscription_price * 100),  # Convert to cents
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }
            ],
            metadata={
                'subscriber_id': request.user.id,
                'creator_id': creator.id,
            },
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        
        return redirect(checkout_session.url)
    
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('creator_profile', username=username)

def checkout_success(request):
    """Handle successful checkout"""
    messages.success(request, _('Your subscription was successful! Enjoy the content.'))
    return redirect('home')

def checkout_cancel(request):
    """Handle cancelled checkout"""
    messages.info(request, _('Your subscription was cancelled.'))
    return redirect('discover')

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve subscription and customer info
        subscriber_id = session['metadata']['subscriber_id']
        creator_id = session['metadata']['creator_id']
        
        # Create subscription in our database
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
                stripe_subscription_id=session['subscription']
            )
            
            # Record the payment
            PaymentHistory.objects.create(
                user=subscriber,
                recipient=creator,
                payment_type='subscription',
                amount=creator.subscription_price,
                status='succeeded',
                stripe_payment_id=session['payment_intent'],
                subscription=subscription
            )
            
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")
            return HttpResponse(status=500)
    
    elif event['type'] == 'invoice.payment_succeeded':
        # Handle successful recurring payment
        invoice = event['data']['object']
        subscription_id = invoice['subscription']
        
        # Update the subscription in our database
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            
            # Update expiration date
            subscription.expires_at = subscription.expires_at + timedelta(days=30)
            subscription.save()
            
            # Record the payment
            PaymentHistory.objects.create(
                user=subscription.subscriber,
                recipient=subscription.creator,
                payment_type='subscription',
                amount=subscription.price,
                status='succeeded',
                stripe_payment_id=invoice['payment_intent'],
                subscription=subscription
            )
            
        except Subscription.DoesNotExist:
            print(f"Subscription not found: {subscription_id}")
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
    
    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription_data = event['data']['object']
        subscription_id = subscription_data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.active = False
            subscription.save()
        except Subscription.DoesNotExist:
            print(f"Subscription not found: {subscription_id}")
    
    return HttpResponse(status=200)
