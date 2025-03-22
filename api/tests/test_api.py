from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from content.models import Post, Category, Tag
from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class APITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
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

    def test_user_registration(self):
        """Test user registration API"""
        response = self.client.post(
            reverse('api:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'testpass123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login API"""
        response = self.client.post(
            reverse('api:login'),
            {
                'username': 'creator',
                'password': 'testpass123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_post_list(self):
        """Test post list API"""
        response = self.client.get(reverse('api:post_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_post_detail(self):
        """Test post detail API"""
        response = self.client.get(
            reverse('api:post_detail', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_post_creation(self):
        """Test post creation API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.post(
            reverse('api:post_list'),
            {
                'title': 'New Post',
                'text': 'New content',
                'visibility': 'public'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title='New Post').exists())

    def test_post_update(self):
        """Test post update API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.patch(
            reverse('api:post_detail', args=[self.post.id]),
            {'title': 'Updated Post'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Post')

    def test_post_deletion(self):
        """Test post deletion API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.delete(
            reverse('api:post_detail', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_subscription_management(self):
        """Test subscription management API"""
        self.client.force_authenticate(user=self.subscriber)
        
        # Create subscription
        response = self.client.post(
            reverse('api:subscription_list'),
            {
                'creator_id': self.creator.id,
                'plan_id': 'price_test123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Cancel subscription
        subscription_id = response.data['id']
        response = self.client.post(
            reverse('api:subscription_cancel', args=[subscription_id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_method_management(self):
        """Test payment method management API"""
        self.client.force_authenticate(user=self.subscriber)
        
        # Add payment method
        response = self.client.post(
            reverse('api:payment_method_list'),
            {
                'stripe_token': 'tok_test123',
                'card_brand': 'visa',
                'last4': '4242'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List payment methods
        response = self.client.get(reverse('api:payment_method_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_notification_list(self):
        """Test notification list API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.get(reverse('api:notification_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_user_profile(self):
        """Test user profile API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.get(
            reverse('api:user_profile', args=[self.creator.id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'creator')

    def test_user_profile_update(self):
        """Test user profile update API"""
        self.client.force_authenticate(user=self.creator)
        
        response = self.client.patch(
            reverse('api:user_profile', args=[self.creator.id]),
            {'bio': 'Updated bio'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.creator.refresh_from_db()
        self.assertEqual(self.creator.bio, 'Updated bio')

    def test_search_api(self):
        """Test search API"""
        response = self.client.get(
            reverse('api:search'),
            {'q': 'test', 'type': 'content'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        for _ in range(100):  # Assuming rate limit is 100 requests per minute
            response = self.client.get(reverse('api:post_list'))
        
        response = self.client.get(reverse('api:post_list'))
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_api_authentication(self):
        """Test API authentication"""
        response = self.client.get(reverse('api:post_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Public endpoint
        
        response = self.client.get(reverse('api:user_profile', args=[self.creator.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Private endpoint

    def test_subscription_creation(self):
        """Test subscription creation API"""
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:subscription-list')
        data = {
            'creator': self.creator.id,
            'plan': 'monthly',
            'payment_method': 'card'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subscription.objects.filter(
            subscriber=self.subscriber,
            creator=self.creator
        ).exists())

    def test_subscription_cancellation(self):
        """Test subscription cancellation API"""
        subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            plan='monthly',
            status='active'
        )
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:subscription-detail', kwargs={'pk': subscription.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'cancelled')

    def test_content_search(self):
        """Test content search API"""
        url = reverse('api:content-search')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_category_list(self):
        """Test category listing API"""
        category = Category.objects.create(name='Test Category')
        url = reverse('api:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_tag_list(self):
        """Test tag listing API"""
        tag = Tag.objects.create(name='test')
        self.post.tags.add(tag)
        url = reverse('api:tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_content_by_category(self):
        """Test content filtering by category"""
        category = Category.objects.create(name='Test Category')
        self.post.category = category
        self.post.save()
        url = reverse('api:content-by-category', kwargs={'category_id': category.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_content_by_tag(self):
        """Test content filtering by tag"""
        tag = Tag.objects.create(name='test')
        self.post.tags.add(tag)
        url = reverse('api:content-by-tag', kwargs={'tag_id': tag.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_creator_stats(self):
        """Test creator statistics API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:creator-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscriber_count', response.data)
        self.assertIn('post_count', response.data)
        self.assertIn('total_revenue', response.data)

    def test_notification_mark_read(self):
        """Test marking notifications as read"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:notification-mark-read')
        data = {'notification_ids': [1, 2, 3]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) 