from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from content.models import Post, Category, Tag
from subscriptions.models import Subscription
from django.utils import timezone

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
        url = reverse('api:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login API"""
        url = reverse('api:login')
        data = {
            'username': 'creator',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_post_list(self):
        """Test post listing API"""
        url = reverse('api:post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_detail(self):
        """Test post detail API"""
        url = reverse('api:post-detail', kwargs={'pk': self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_post_creation(self):
        """Test post creation API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-list')
        data = {
            'title': 'New Post',
            'text': 'New content',
            'visibility': 'public'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)

    def test_post_update(self):
        """Test post update API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-detail', kwargs={'pk': self.post.id})
        data = {
            'title': 'Updated Post',
            'text': 'Updated content'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Post')

    def test_post_deletion(self):
        """Test post deletion API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:post-detail', kwargs={'pk': self.post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

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

    def test_user_profile(self):
        """Test user profile API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'creator')

    def test_user_profile_update(self):
        """Test user profile update API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:user-profile')
        data = {
            'bio': 'Updated bio',
            'location': 'New York'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.creator.profile.refresh_from_db()
        self.assertEqual(self.creator.profile.bio, 'Updated bio')

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

    def test_notification_list(self):
        """Test notification listing API"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_mark_read(self):
        """Test marking notifications as read"""
        self.client.force_authenticate(user=self.creator)
        url = reverse('api:notification-mark-read')
        data = {'notification_ids': [1, 2, 3]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) 