from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from subscriptions.models import SavedPaymentMethod
from unittest.mock import patch, MagicMock
import stripe
import json

User = get_user_model()

class PaymentMethodsTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Mock Stripe payment method data
        self.stripe_payment_method = {
            'id': 'pm_test123',
            'card': {
                'last4': '4242',
                'brand': 'visa',
                'exp_month': 12,
                'exp_year': 2025
            }
        }

    def test_list_payment_methods_view(self):
        """Test the payment methods listing view"""
        # Create a test payment method
        SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        # Get the payment methods page
        response = self.client.get(reverse('subscriptions:list_payment_methods'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/payment_methods.html')
        self.assertContains(response, '4242')  # Check if card number is displayed
        self.assertContains(response, 'visa')  # Check if card brand is displayed

    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.PaymentMethod.attach')
    def test_save_payment_method(self, mock_attach, mock_retrieve):
        """Test saving a new payment method"""
        # Mock Stripe API responses
        mock_card = MagicMock(
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025
        )
        mock_payment_method = MagicMock(
            id='pm_test123',
            card=mock_card
        )
        mock_retrieve.return_value = mock_payment_method
        mock_attach.return_value = mock_payment_method

        # Set Stripe customer ID for the user
        self.user.stripe_customer_id = 'cus_test123'
        self.user.save()

        # Send request to save payment method
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Check database
        payment_method = SavedPaymentMethod.objects.get(user=self.user)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test123')
        self.assertEqual(payment_method.last4, '4242')
        self.assertEqual(payment_method.brand, 'visa')
        self.assertTrue(payment_method.is_default)  # Should be default as it's the first card

        # Verify that the Stripe API was called correctly
        mock_retrieve.assert_called_once_with('pm_test123')

    @patch('stripe.PaymentMethod.retrieve')
    def test_save_payment_method_invalid_data(self, mock_retrieve):
        """Test saving a payment method with invalid data"""
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({}),  # Empty data
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Payment method ID is required')

    def test_set_default_payment_method(self):
        """Test setting a payment method as default"""
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

        # Set second payment method as default
        response = self.client.post(
            reverse('subscriptions:set_default_payment_method'),
            data=json.dumps({'payment_method_id': pm2.id}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Refresh from database
        pm1.refresh_from_db()
        pm2.refresh_from_db()

        # Check that default status was updated
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)

    @patch('stripe.PaymentMethod.detach')
    def test_delete_payment_method(self, mock_detach):
        """Test deleting a payment method"""
        # Create a payment method to delete
        payment_method = SavedPaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            last4='4242',
            brand='visa',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )

        # Delete the payment method
        response = self.client.post(
            reverse('subscriptions:delete_payment_method'),
            data=json.dumps({'payment_method_id': payment_method.id}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Check that the payment method was deleted
        self.assertEqual(SavedPaymentMethod.objects.count(), 0)
        mock_detach.assert_called_once_with('pm_test123')

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access payment methods"""
        # Logout the user
        self.client.logout()

        # Try to access payment methods page
        response = self.client.get(reverse('subscriptions:list_payment_methods'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        # Try to save a payment method
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_payment_method_model(self):
        """Test the SavedPaymentMethod model"""
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
        self.assertTrue(payment_method.is_expired(2026, 1))  # Test expiration check
        self.assertFalse(payment_method.is_expired(2024, 12))  # Test not expired

    @patch('stripe.PaymentMethod.retrieve')
    def test_stripe_error_handling(self, mock_retrieve):
        """Test handling of Stripe API errors"""
        # Mock Stripe error
        mock_retrieve.side_effect = stripe.error.StripeError('Stripe API error')

        # Try to save payment method
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Stripe API error') 