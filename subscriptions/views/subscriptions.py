from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
from accounts.models import User
from subscriptions.models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscribe(request, creator_username):
    """View to handle subscription to a creator"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    # Check if user is trying to subscribe to themselves
    if request.user == creator:
        return JsonResponse({
            'success': False,
            'message': 'You cannot subscribe to yourself'
        }, status=400)
    
    # Check if already subscribed
    existing_subscription = Subscription.objects.filter(
        subscriber=request.user,
        creator=creator,
        status='active'
    ).first()
    
    if existing_subscription:
        return JsonResponse({
            'success': False,
            'message': 'You are already subscribed to this creator'
        }, status=400)
    
    try:
        # Create or get Stripe customer for subscriber
        if not request.user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={
                    'user_id': request.user.id,
                    'username': request.user.username
                }
            )
            request.user.stripe_customer_id = customer.id
            request.user.save()
        
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(creator.subscription_price * 100),  # Convert to cents
            currency='usd',
            customer=request.user.stripe_customer_id,
            metadata={
                'creator_id': creator.id,
                'creator_username': creator.username,
                'subscriber_id': request.user.id,
                'subscriber_username': request.user.username
            }
        )
        
        return render(request, 'subscriptions/subscribe.html', {
            'creator': creator,
            'client_secret': payment_intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def cancel_subscription(request, creator_username):
    """View to cancel a subscription"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    try:
        subscription = Subscription.objects.get(
            subscriber=request.user,
            creator=creator,
            status='active'
        )
        
        # Cancel the subscription in Stripe
        stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update subscription status
        subscription.status = 'cancelled'
        subscription.cancellation_reason = request.POST.get('cancellation_reason')
        subscription.save()
        
        return redirect('subscriptions:subscription_confirmation', creator_username=creator_username)
        
    except Subscription.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No active subscription found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def subscription_confirmation(request, creator_username):
    """View to show subscription confirmation"""
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    subscription = Subscription.objects.filter(
        subscriber=request.user,
        creator=creator,
        status='active'
    ).first()
    
    return render(request, 'subscriptions/subscription_confirmation.html', {
        'creator': creator,
        'subscription': subscription
    })

@require_POST
def stripe_webhook(request):
    """View to handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        creator_username = payment_intent['metadata']['creator_username']
        subscriber_id = payment_intent['metadata']['subscriber_id']
        
        creator = User.objects.get(username=creator_username)
        subscriber = User.objects.get(id=subscriber_id)
        
        # Create subscription
        subscription = Subscription.objects.create(
            subscriber=subscriber,
            creator=creator,
            stripe_subscription_id=payment_intent['id'],
            status='active'
        )
    
    return JsonResponse({'status': 'success'}) 