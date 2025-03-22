from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from subscriptions.models import SavedPaymentMethod
from unittest.mock import patch, MagicMock
import stripe
import json

User = get_user_model()

class PaymentMethodsIntegrationTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            stripe_customer_id='cus_test123'  # Add Stripe customer ID
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.PaymentMethod.attach')
    def test_full_payment_method_lifecycle(self, mock_attach, mock_retrieve):
        """Test the complete lifecycle of a payment method"""
        # Mock Stripe API responses
        mock_retrieve.return_value = MagicMock(
            id='pm_test123',
            card=MagicMock(
                last4='4242',
                brand='visa',
                exp_month=12,
                exp_year=2025
            )
        )
        mock_attach.return_value = mock_retrieve.return_value

        # 1. Add a new payment method
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verify the payment method was saved
        payment_method = SavedPaymentMethod.objects.get(user=self.user)
        self.assertEqual(payment_method.last4, '4242')
        self.assertTrue(payment_method.is_default)

        # 2. Add a second payment method
        mock_retrieve.return_value = MagicMock(
            id='pm_test456',
            card=MagicMock(
                last4='5555',
                brand='mastercard',
                exp_month=1,
                exp_year=2026
            )
        )
        mock_attach.return_value = mock_retrieve.return_value

        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test456'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 3. Set the second payment method as default
        second_payment_method = SavedPaymentMethod.objects.get(last4='5555')
        response = self.client.post(
            reverse('subscriptions:set_default_payment_method'),
            data=json.dumps({'payment_method_id': second_payment_method.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Verify default was updated
        payment_method.refresh_from_db()
        second_payment_method.refresh_from_db()
        self.assertFalse(payment_method.is_default)
        self.assertTrue(second_payment_method.is_default)

        # 4. View the payment methods list
        response = self.client.get(reverse('subscriptions:list_payment_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '4242')
        self.assertContains(response, '5555')

        # 5. Delete the first payment method
        with patch('stripe.PaymentMethod.detach') as mock_detach:
            response = self.client.post(
                reverse('subscriptions:delete_payment_method'),
                data=json.dumps({'payment_method_id': payment_method.id}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            mock_detach.assert_called_once_with('pm_test123')

        # Verify the payment method was deleted
        self.assertEqual(SavedPaymentMethod.objects.count(), 1)
        self.assertEqual(SavedPaymentMethod.objects.first(), second_payment_method)

    @patch('stripe.PaymentMethod.retrieve')
    def test_error_handling_flow(self, mock_retrieve):
        """Test error handling throughout the payment method lifecycle"""
        # 1. Test invalid payment method ID
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)['success'])

        # 2. Test Stripe API error
        mock_retrieve.side_effect = stripe.error.StripeError('Invalid card')
        response = self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['message'], 'Invalid card')

        # 3. Test invalid payment method ID for setting default
        response = self.client.post(
            reverse('subscriptions:set_default_payment_method'),
            data=json.dumps({'payment_method_id': 999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

        # 4. Test deleting non-existent payment method
        response = self.client.post(
            reverse('subscriptions:delete_payment_method'),
            data=json.dumps({'payment_method_id': 999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_concurrent_default_payment_methods(self):
        """Test handling of concurrent default payment method updates"""
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

        # Simulate concurrent updates
        def update_default(payment_method_id):
            return self.client.post(
                reverse('subscriptions:set_default_payment_method'),
                data=json.dumps({'payment_method_id': payment_method_id}),
                content_type='application/json'
            )

        response1 = update_default(pm1.id)
        response2 = update_default(pm2.id)

        # Both requests should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # But only one payment method should be default
        self.assertEqual(SavedPaymentMethod.objects.filter(is_default=True).count(), 1)

    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.PaymentMethod.attach')
    def test_customer_payment_method_isolation(self, mock_attach, mock_retrieve):
        """Test that payment methods are properly isolated between customers"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            stripe_customer_id='cus_test456'
        )

        # Mock Stripe API response
        mock_retrieve.return_value = MagicMock(
            id='pm_test123',
            card=MagicMock(
                last4='4242',
                brand='visa',
                exp_month=12,
                exp_year=2025
            )
        )
        mock_attach.return_value = mock_retrieve.return_value

        # Add payment method for first user
        self.client.post(
            reverse('subscriptions:save_payment_method'),
            data=json.dumps({'payment_method_id': 'pm_test123'}),
            content_type='application/json'
        )

        # Switch to other user
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')

        # Try to access first user's payment method
        payment_method = SavedPaymentMethod.objects.get(user=self.user)
        response = self.client.post(
            reverse('subscriptions:set_default_payment_method'),
            data=json.dumps({'payment_method_id': payment_method.id}),
            content_type='application/json'
        )

        # Should fail with 404 as the payment method doesn't belong to other_user
        self.assertEqual(response.status_code, 404) 