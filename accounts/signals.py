from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
import stripe
from django.conf import settings
from .models import User

stripe.api_key = settings.STRIPE_SECRET_KEY

@receiver(user_logged_in)
def create_stripe_customer(sender, user, request, **kwargs):
    """
    Create a Stripe customer for the user if they don't have one when they log in.
    """
    # Check if the user model has the stripe_customer_id field
    if hasattr(user, 'stripe_customer_id'):
        if not user.stripe_customer_id:
            try:
                # Create a new Stripe customer
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={
                        'user_id': user.id,
                        'username': user.username
                    }
                )
                
                # Save the customer ID to the user's profile
                user.stripe_customer_id = customer.id
                user.save()
                
            except stripe.error.StripeError as e:
                # Log the error but don't prevent login
                print(f"Error creating Stripe customer for user {user.username}: {str(e)}") 