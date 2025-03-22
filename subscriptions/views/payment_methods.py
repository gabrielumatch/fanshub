from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
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
        # Get the payment method ID from the request
        payment_method_id = request.POST.get('payment_method_id')
        
        # Retrieve the payment method from Stripe
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        
        # Create a new saved payment method
        saved_method = SavedPaymentMethod.objects.create(
            user=request.user,
            stripe_payment_method_id=payment_method_id,
            last4=payment_method.card.last4,
            brand=payment_method.card.brand,
            exp_month=payment_method.card.exp_month,
            exp_year=payment_method.card.exp_year,
            is_default=not SavedPaymentMethod.objects.filter(user=request.user).exists()
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
        payment_method_id = request.POST.get('payment_method_id')
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
        payment_method_id = request.POST.get('payment_method_id')
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
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 