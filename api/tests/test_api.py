from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from content.models import Post, Media, Category, Tag
from subscriptions.models import Subscription
from payments.models import PaymentMethod
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta
import json

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
        self.category = Category.objects.create(name='Test Category')
        self.tag = Tag.objects.create(name='test_tag')
        self.post.categories.add(self.category)
        self.post.tags.add(self.tag)

    def test_user_registration(self):
        """Test user registration API"""
        url = reverse('api:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'is_creator': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)  # creator + subscriber + new user
        self.assertEqual(User.objects.get(username='newuser').email, 'newuser@example.com')

    def test_user_login(self):
        """Test user login API"""
        url = reverse('api:login')
        data = {
            'username': 'subscriber',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_post_list(self):
        """Test post listing API"""
        url = reverse('api:post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Post')

    def test_post_detail(self):
        """Test post detail API"""
        url = reverse('api:post-detail', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')
        self.assertEqual(response.data['text'], 'Test content')

    def test_post_creation(self):
        """Test post creation API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-list')
        data = {
            'title': 'New Post',
            'text': 'New content',
            'visibility': 'public',
            'categories': [self.category.id],
            'tags': [self.tag.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Post.objects.get(title='New Post').text, 'New content')

    def test_post_update(self):
        """Test post update API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-detail', args=[self.post.id])
        data = {
            'title': 'Updated Post',
            'text': 'Updated content'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Post')
        self.assertEqual(self.post.text, 'Updated content')

    def test_post_deletion(self):
        """Test post deletion API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-detail', args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_subscription_management(self):
        """Test subscription management API"""
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:subscription-list')
        
        # Create subscription
        data = {
            'creator': self.creator.id,
            'plan': 'monthly',
            'payment_method': 'card'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List subscriptions
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Cancel subscription
        subscription_id = response.data['results'][0]['id']
        url = reverse('api:subscription-detail', args=[subscription_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_payment_method_management(self):
        """Test payment method management API"""
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:payment-method-list')
        
        # Add payment method
        data = {
            'type': 'card',
            'card_number': '4242424242424242',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvc': '123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List payment methods
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Delete payment method
        method_id = response.data['results'][0]['id']
        url = reverse('api:payment-method-detail', args=[method_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentMethod.objects.count(), 0)

    def test_notification_list(self):
        """Test notification listing API"""
        self.client.force_authenticate(user=self.subscriber)
        
        # Create notification
        Notification.objects.create(
            recipient=self.subscriber,
            notification_type='like',
            content_object=self.post
        )
        
        url = reverse('api:notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['notification_type'], 'like')

    def test_user_profile(self):
        """Test user profile API"""
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'subscriber')
        self.assertEqual(response.data['email'], 'subscriber@example.com')

    def test_user_profile_update(self):
        """Test user profile update API"""
        self.client.force_authenticate(user=self.subscriber)
        url = reverse('api:user-profile')
        data = {
            'bio': 'Updated bio',
            'location': 'New York'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscriber.refresh_from_db()
        self.assertEqual(self.subscriber.profile.bio, 'Updated bio')
        self.assertEqual(self.subscriber.profile.location, 'New York')

    def test_search_api(self):
        """Test search API"""
        url = reverse('api:search')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertIn('creators', response.data)
        self.assertEqual(len(response.data['posts']), 1)
        self.assertEqual(len(response.data['creators']), 1)

    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        url = reverse('api:post-list')
        for _ in range(100):  # Assuming rate limit is less than 100 requests
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_api_authentication(self):
        """Test API authentication"""
        url = reverse('api:post-list')
        
        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Public endpoint
        
        # Test authenticated access
        self.client.force_authenticate(user=self.subscriber)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test protected endpoint
        url = reverse('api:user-profile')
        self.client.force_authenticate(user=None)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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