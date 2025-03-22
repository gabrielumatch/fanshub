from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from subscriptions.models import SavedPaymentMethod
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import IntegrityError
from django.core.exceptions import ValidationError

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
            stripe_payment_method_id='pm_test123',
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
        expected_str = 'visa **** 4242'
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

class SavedPaymentMethodModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_payment_method(self):
        """Test creating a payment method"""
        payment_method = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        self.assertEqual(payment_method.user, self.user)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test123')
        self.assertEqual(payment_method.last4, '4242')
        self.assertEqual(payment_method.brand, 'visa')
        self.assertEqual(payment_method.exp_month, 12)
        self.assertEqual(payment_method.exp_year, 2025)
        self.assertTrue(payment_method.is_default)

    def test_payment_method_str_representation(self):
        """Test the string representation of a payment method"""
        payment_method = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        self.assertEqual(str(payment_method), 'visa **** 4242')
        self.assertEqual(payment_method.get_card_display(), 'visa **** 4242')

    def test_payment_method_unique_constraint(self):
        """Test that stripe_payment_method_id must be unique"""
        # Create first payment method
        SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025
        )

        # Try to create another payment method with the same stripe_payment_method_id
        with self.assertRaises(ValidationError):
            SavedPaymentMethod.objects.create(
                user=self.user,
                stripe_payment_method_id='pm_test123',  # Same ID
                last4='5555',
                brand='mastercard',
                exp_month=1,
                exp_year=2026
            )

    def test_payment_method_expiration(self):
        """Test payment method expiration checks"""
        payment_method = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025
        )

        # Test expired
        self.assertTrue(payment_method.is_expired(2026, 1))
        self.assertTrue(payment_method.is_expired(2025, 13))  # Month after expiration
        
        # Test not expired
        self.assertFalse(payment_method.is_expired(2024, 12))
        self.assertFalse(payment_method.is_expired(2025, 12))  # Same month
        self.assertFalse(payment_method.is_expired(2025, 1))  # Earlier month same year

    def test_default_payment_method_logic(self):
        """Test that only one payment method can be default"""
        # Create first payment method (default)
        pm1 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        # Create second payment method (not default)
        pm2 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test456',
            last4='5555',
            brand='mastercard',
            exp_month=1,
            exp_year=2026,
            is_default=False
        )

        # Set second payment method as default
        pm2.is_default = True
        pm2.save()

        # Refresh from database
        pm1.refresh_from_db()
        pm2.refresh_from_db()

        # Check that first payment method is no longer default
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)

    def test_payment_method_validation(self):
        """Test payment method validation"""
        # Test invalid expiration month
        with self.assertRaises(ValidationError):
            payment_method = SavedPaymentMethod(
                user=self.user,
                stripe_payment_method_id='pm_test123',
                last4='4242',
                brand='visa',
                exp_month=13,  # Invalid month
                exp_year=2025
            )
            payment_method.full_clean()

        # Test invalid expiration year
        with self.assertRaises(ValidationError):
            payment_method = SavedPaymentMethod(
                user=self.user,
                stripe_payment_method_id='pm_test123',
                last4='4242',
                brand='visa',
                exp_month=12,
                exp_year=1999  # Past year
            )
            payment_method.full_clean()

        # Test invalid last4
        with self.assertRaises(ValidationError):
            payment_method = SavedPaymentMethod(
                user=self.user,
                stripe_payment_method_id='pm_test123',
                last4='123',  # Too short
                brand='visa',
                exp_month=12,
                exp_year=2025
            )
            payment_method.full_clean()

    def test_auto_set_first_card_as_default(self):
        """Test that the first card added is automatically set as default"""
        # Create first payment method without specifying default
        pm1 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025
        )

        # Check that it was automatically set as default
        self.assertTrue(pm1.is_default)

        # Create second payment method
        pm2 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test456',
            last4='5555',
            brand='mastercard',
            exp_month=1,
            exp_year=2026
        )

        # Check that it was not automatically set as default
        self.assertFalse(pm2.is_default)

    def test_delete_default_payment_method(self):
        """Test deleting the default payment method"""
        # Create two payment methods
        pm1 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        pm2 = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test456',
            last4='5555',
            brand='mastercard',
            exp_month=1,
            exp_year=2026,
            is_default=False
        )

        # Delete the default payment method
        pm1.delete()

        # Refresh the second payment method from database
        pm2.refresh_from_db()

        # Check that the second payment method is now default
        self.assertTrue(pm2.is_default) 