from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.exceptions import ValidationError
import stripe
import json
from subscriptions.models import SavedPaymentMethod

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def list_payment_methods(request):
    """View to list user's saved payment methods"""
    payment_methods = SavedPaymentMethod.objects.filter(user=request.user)
    return render(request, 'subscriptions/payment_methods.html', {
        'payment_methods': payment_methods,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })

@login_required
@require_POST
def save_payment_method(request):
    """View to save a new payment method"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return JsonResponse({
                'success': False,
                'message': 'Payment method ID is required'
            }, status=400)
        
        # Retrieve the payment method from Stripe
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        
        # Attach the payment method to the customer if they have a Stripe customer ID
        if request.user.stripe_customer_id:
            try:
                payment_method = stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=request.user.stripe_customer_id,
                )
            except stripe.error.StripeError as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
        
        # Check if this payment method already exists for this user
        if SavedPaymentMethod.objects.filter(
            user=request.user,
            stripe_payment_method_id=payment_method_id
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'This payment method has already been saved'
            }, status=400)
        
        try:
            # Create a new saved payment method
            saved_method = SavedPaymentMethod.objects.create(
                user=request.user,
                stripe_payment_method_id=payment_method_id,
                last4=payment_method.card.last4,
                brand=payment_method.card.brand,
                exp_month=payment_method.card.exp_month,
                exp_year=payment_method.card.exp_year
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Payment method saved successfully',
                'payment_method': {
                    'id': saved_method.id,
                    'last4': saved_method.last4,
                    'brand': saved_method.brand,
                    'exp_month': saved_method.exp_month,
                    'exp_year': saved_method.exp_year,
                    'is_default': saved_method.is_default
                }
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def set_default_payment_method(request):
    """View to set a payment method as default"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return JsonResponse({
                'success': False,
                'message': 'Payment method ID is required'
            }, status=400)
        
        payment_method = SavedPaymentMethod.objects.get(
            id=payment_method_id,
            user=request.user
        )
        
        # Set as default (this will automatically unset others)
        payment_method.is_default = True
        payment_method.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Default payment method updated successfully'
        })
    except SavedPaymentMethod.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment method not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def delete_payment_method(request):
    """View to delete a saved payment method"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return JsonResponse({
                'success': False,
                'message': 'Payment method ID is required'
            }, status=400)
        
        payment_method = SavedPaymentMethod.objects.get(
            id=payment_method_id,
            user=request.user
        )
        
        # Delete the payment method from Stripe
        stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
        
        # Delete from our database
        payment_method.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment method deleted successfully'
        })
    except SavedPaymentMethod.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment method not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 