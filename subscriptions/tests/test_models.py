from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from subscriptions.models import SavedPaymentMethod

User = get_user_model()

class SavedPaymentMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.payment_method = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test_123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

    def test_saved_payment_method_creation(self):
        """Test creating a saved payment method"""
        self.assertEqual(self.payment_method.user, self.user)
        self.assertEqual(self.payment_method.last4, '4242')
        self.assertEqual(self.payment_method.brand, 'visa')
        self.assertTrue(self.payment_method.is_default)

    def test_default_payment_method_behavior(self):
        """Test that setting a payment method as default unsets others"""
        # Create another payment method
        other_payment = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test_456',
            last4='8888',
            brand='mastercard',
            exp_month=12,
            exp_year=2025,
            is_default=False
        )

        # Set the other payment method as default
        other_payment.is_default = True
        other_payment.save()

        # Refresh the original payment method from database
        self.payment_method.refresh_from_db()
        
        # Check that the original is no longer default
        self.assertFalse(self.payment_method.is_default)
        # Check that the new one is default
        self.assertTrue(other_payment.is_default)

    def test_payment_method_str_representation(self):
        """Test the string representation of a payment method"""
        expected_str = f"{self.user.username}'s visa card ending in 4242"
        self.assertEqual(str(self.payment_method), expected_str)

    def test_payment_method_ordering(self):
        """Test that payment methods are ordered by default status and creation date"""
        # Create another payment method
        SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test_789',
            last4='1111',
            brand='amex',
            exp_month=12,
            exp_year=2025,
            is_default=False
        )

        # Get all payment methods for the user
        payment_methods = SavedPaymentMethod.objects.filter(user=self.user)
        
        # Check that the default payment method is first
        self.assertEqual(payment_methods[0], self.payment_method) 