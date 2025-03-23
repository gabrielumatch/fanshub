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
def check_subscription(request, subscription_id):
    """API endpoint to check subscription status"""
    print(f"\n=== Checking subscription status for {subscription_id} ===")
    
    try:
        # First check our database
        print("Checking local database for subscription")
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        print(f"Found subscription in database: {subscription.id}")
        print(f"Subscription status: active={subscription.active}")
        return JsonResponse({
            'active': subscription.active
        })
    except Subscription.DoesNotExist:
        print("Subscription not found in database, checking Stripe...")
        try:
            # If not in our database, check Stripe
            print(f"Retrieving subscription from Stripe: {subscription_id}")
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            print(f"Found subscription in Stripe. Status: {stripe_subscription.status}")
            print(f"Stripe subscription metadata: {stripe_subscription.metadata}")
            
            # Check if the subscription is in a valid state
            if stripe_subscription.status in ['active', 'trialing']:
                print("Subscription is active or trialing, creating in database...")
                # Create subscription in our database
                creator_username = stripe_subscription.metadata['creator_username']
                subscriber_id = stripe_subscription.metadata['subscriber_id']
                
                print(f"Looking up creator: {creator_username}")
                creator = User.objects.get(username=creator_username)
                print(f"Looking up subscriber: {subscriber_id}")
                subscriber = User.objects.get(id=subscriber_id)
                
                # Calculate expiration date (1 month from now)
                from django.utils import timezone
                from datetime import timedelta
                expires_at = timezone.now() + timedelta(days=30)
                
                print("Creating subscription in database")
                subscription = Subscription.objects.create(
                    subscriber=subscriber,
                    creator=creator,
                    stripe_subscription_id=subscription_id,
                    active=True,
                    expires_at=expires_at,
                    price=creator.subscription_price,
                    auto_renew=True
                )
                print(f"Created subscription in database: {subscription.id}")
                
                return JsonResponse({
                    'active': True
                })
            elif stripe_subscription.status == 'incomplete':
                print("Subscription is incomplete, payment still processing...")
                # Payment is still processing
                return JsonResponse({
                    'active': False,
                    'status': 'processing'
                })
            else:
                print(f"Subscription is in invalid state: {stripe_subscription.status}")
                # Subscription is in an invalid state
                return JsonResponse({
                    'active': False,
                    'status': stripe_subscription.status
                })
                
        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            return JsonResponse({
                'active': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'active': False,
                'error': str(e)
            }, status=500)
        
        print("Subscription not found in Stripe")
        return JsonResponse({
            'active': False,
            'status': 'not_found'
        }, status=404)

@login_required
def subscribe(request, creator_username):
    """View to handle subscription to a creator"""
    print(f"\n=== Starting subscription process for {creator_username} ===")
    creator = get_object_or_404(User, username=creator_username, is_creator=True)
    
    # Check if user is trying to subscribe to themselves
    if request.user == creator:
        print("Error: User trying to subscribe to themselves")
        return JsonResponse({
            'success': False,
            'message': 'You cannot subscribe to yourself'
        }, status=400)
    
    # Check if already subscribed
    existing_subscription = Subscription.objects.filter(
        subscriber=request.user,
        creator=creator,
        active=True
    ).first()
    
    if existing_subscription:
        print(f"Error: User already subscribed (Subscription ID: {existing_subscription.id})")
        return JsonResponse({
            'success': False,
            'message': 'You are already subscribed to this creator'
        }, status=400)
    
    try:
        print(f"Creating subscription for user {request.user.username} to creator {creator.username}")
        
        # Create or get Stripe customer for subscriber
        if not request.user.stripe_customer_id:
            print("Creating new Stripe customer for subscriber")
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={
                    'user_id': request.user.id,
                    'username': request.user.username
                }
            )
            request.user.stripe_customer_id = customer.id
            request.user.save()
            print(f"Created Stripe customer: {customer.id}")
        else:
            print(f"Using existing Stripe customer: {request.user.stripe_customer_id}")
        
        # Create or get Stripe product for creator
        if not creator.stripe_product_id:
            print("Creating new Stripe product for creator")
            product = stripe.Product.create(
                name=f"Subscription to {creator.username}",
                metadata={
                    'creator_id': creator.id,
                    'creator_username': creator.username
                }
            )
            creator.stripe_product_id = product.id
            creator.save()
            print(f"Created Stripe product: {product.id}")
        else:
            print(f"Using existing Stripe product: {creator.stripe_product_id}")
        
        # Create or get Stripe price for creator
        if not creator.stripe_price_id:
            print("Creating new Stripe price for creator")
            price = stripe.Price.create(
                product=creator.stripe_product_id,
                unit_amount=int(creator.subscription_price * 100),  # Convert to cents
                currency='usd',
                recurring={'interval': 'month'}
            )
            creator.stripe_price_id = price.id
            creator.save()
            print(f"Created Stripe price: {price.id}")
        else:
            print(f"Using existing Stripe price: {creator.stripe_price_id}")
        
        # Create subscription
        print("Creating Stripe subscription")
        subscription = stripe.Subscription.create(
            customer=request.user.stripe_customer_id,
            items=[{'price': creator.stripe_price_id}],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
            metadata={
                'creator_id': creator.id,
                'creator_username': creator.username,
                'subscriber_id': request.user.id,
                'subscriber_username': request.user.username
            }
        )
        print(f"Created Stripe subscription: {subscription.id}")
        print(f"Payment intent client secret: {subscription.latest_invoice.payment_intent.client_secret}")
        
        return render(request, 'subscriptions/subscribe.html', {
            'creator': creator,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'subscription_id': subscription.id,
            'debug': settings.DEBUG
        })
        
    except Exception as e:
        print(f"Error in subscribe view: {str(e)}")
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
            active=True
        )
        
        # Cancel the subscription in Stripe
        stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update subscription status
        subscription.active = False
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
        active=True
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
        creator_id = payment_intent['metadata']['creator_id']
        subscriber_id = payment_intent['metadata']['subscriber_id']
        
        try:
            subscriber = User.objects.get(id=subscriber_id)
            creator = User.objects.get(id=creator_id)
            
            # Create subscription in Stripe
            subscription = stripe.Subscription.create(
                customer=subscriber.stripe_customer_id,
                items=[{'price': creator.stripe_price_id}],
                metadata={
                    'creator_id': creator.id,
                    'creator_username': creator.username,
                    'subscriber_id': subscriber.id,
                    'subscriber_username': subscriber.username
                }
            )
            
            # Create subscription in our database
            db_subscription = Subscription.objects.create(
                subscriber=subscriber,
                creator=creator,
                stripe_subscription_id=subscription.id,
                active=True
            )
            
            print(f"Created subscription in database: {db_subscription.id}")  # Debug log
            
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")  # Debug log
            return JsonResponse({'error': str(e)}, status=500)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        try:
            db_subscription = Subscription.objects.get(stripe_subscription_id=subscription['id'])
            db_subscription.active = False
            db_subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    return JsonResponse({'status': 'success'}) 