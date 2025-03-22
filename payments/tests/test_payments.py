from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from payments.models import PaymentMethod, Subscription, Transaction
from content.models import Post
import stripe
from unittest.mock import patch

User = get_user_model()

class PaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123',
            is_creator=True
        )
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            creator=self.creator,
            title='Test Post',
            text='Test content',
            visibility='public'
        )

    @patch('stripe.Customer.create')
    def test_add_payment_method(self, mock_stripe_customer):
        """Test adding a payment method"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Mock Stripe response
        mock_stripe_customer.return_value = {
            'id': 'cus_test123',
            'sources': {
                'data': [{
                    'id': 'card_test123',
                    'brand': 'visa',
                    'last4': '4242'
                }]
            }
        }
        
        response = self.client.post(
            reverse('payments:add_payment_method'),
            {
                'stripe_token': 'tok_test123',
                'card_brand': 'visa',
                'last4': '4242'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PaymentMethod.objects.filter(
            user=self.subscriber,
            stripe_payment_method_id='card_test123'
        ).exists())

    @patch('stripe.Subscription.create')
    def test_create_subscription(self, mock_stripe_subscription):
        """Test creating a subscription"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create payment method
        payment_method = PaymentMethod.objects.create(
            user=self.subscriber,
            stripe_payment_method_id='card_test123',
            card_brand='visa',
            last4='4242'
        )
        
        # Mock Stripe response
        mock_stripe_subscription.return_value = {
            'id': 'sub_test123',
            'status': 'active',
            'current_period_end': 1234567890
        }
        
        response = self.client.post(
            reverse('payments:subscribe', args=[self.creator.id]),
            {
                'payment_method_id': payment_method.id,
                'plan_id': 'price_test123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscription.objects.filter(
            subscriber=self.subscriber,
            creator=self.creator,
            stripe_subscription_id='sub_test123'
        ).exists())

    @patch('stripe.Subscription.delete')
    def test_cancel_subscription(self, mock_stripe_subscription_delete):
        """Test canceling a subscription"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create subscription
        subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            stripe_subscription_id='sub_test123',
            status='active'
        )
        
        response = self.client.post(
            reverse('payments:cancel_subscription', args=[subscription.id])
        )
        
        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'canceled')
        mock_stripe_subscription_delete.assert_called_once()

    @patch('stripe.PaymentIntent.create')
    def test_process_one_time_payment(self, mock_stripe_payment):
        """Test processing a one-time payment"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Mock Stripe response
        mock_stripe_payment.return_value = {
            'id': 'pi_test123',
            'status': 'succeeded',
            'amount': 1000
        }
        
        response = self.client.post(
            reverse('payments:process_payment'),
            {
                'amount': 1000,
                'currency': 'usd',
                'payment_method_id': 'card_test123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Transaction.objects.filter(
            user=self.subscriber,
            stripe_payment_intent_id='pi_test123',
            amount=1000
        ).exists())

    def test_subscription_status_check(self):
        """Test checking subscription status"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create active subscription
        Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            stripe_subscription_id='sub_test123',
            status='active'
        )
        
        response = self.client.get(
            reverse('payments:subscription_status', args=[self.creator.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'active')

    def test_payment_method_list(self):
        """Test listing payment methods"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create payment methods
        PaymentMethod.objects.create(
            user=self.subscriber,
            stripe_payment_method_id='card_test123',
            card_brand='visa',
            last4='4242'
        )
        PaymentMethod.objects.create(
            user=self.subscriber,
            stripe_payment_method_id='card_test456',
            card_brand='mastercard',
            last4='8888'
        )
        
        response = self.client.get(reverse('payments:payment_methods'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['payment_methods']), 2)

    @patch('stripe.PaymentMethod.detach')
    def test_remove_payment_method(self, mock_stripe_detach):
        """Test removing a payment method"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create payment method
        payment_method = PaymentMethod.objects.create(
            user=self.subscriber,
            stripe_payment_method_id='card_test123',
            card_brand='visa',
            last4='4242'
        )
        
        response = self.client.delete(
            reverse('payments:remove_payment_method', args=[payment_method.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PaymentMethod.objects.filter(id=payment_method.id).exists())
        mock_stripe_detach.assert_called_once()

    def test_transaction_history(self):
        """Test viewing transaction history"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create transactions
        Transaction.objects.create(
            user=self.subscriber,
            stripe_payment_intent_id='pi_test123',
            amount=1000,
            status='succeeded'
        )
        Transaction.objects.create(
            user=self.subscriber,
            stripe_payment_intent_id='pi_test456',
            amount=2000,
            status='failed'
        )
        
        response = self.client.get(reverse('payments:transaction_history'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['transactions']), 2)

    @patch('stripe.Invoice.retrieve')
    def test_invoice_retrieval(self, mock_stripe_invoice):
        """Test retrieving invoice details"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Mock Stripe response
        mock_stripe_invoice.return_value = {
            'id': 'in_test123',
            'amount_due': 1000,
            'status': 'paid'
        }
        
        response = self.client.get(
            reverse('payments:invoice_details', args=['in_test123'])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['amount_due'], 1000)
        self.assertEqual(response.json()['status'], 'paid')

    def test_payment_webhook(self):
        """Test handling payment webhooks"""
        # Create test webhook payload
        webhook_payload = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test123',
                    'amount': 1000,
                    'customer': 'cus_test123'
                }
            }
        }
        
        response = self.client.post(
            reverse('payments:webhook'),
            webhook_payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Transaction.objects.filter(
            stripe_payment_intent_id='pi_test123',
            amount=1000
        ).exists()) 