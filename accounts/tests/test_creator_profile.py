from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
from subscriptions.models import Subscription

User = get_user_model()

class CreatorProfileTests(TestCase):
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
        self.creator_profile_url = reverse('creator_profile', kwargs={'username': 'creator'})

    def test_creator_profile_loads(self):
        """Test that creator profile page loads correctly"""
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/creator_profile.html')
        self.assertEqual(response.context['creator'], self.creator)

    def test_creator_profile_with_posts(self):
        """Test creator profile displays posts correctly"""
        # Create a test post
        post = Post.objects.create(
            creator=self.creator,
            title='Test Post',
            text='Test content',
            visibility='public'
        )
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(post, response.context['posts'])

    def test_creator_profile_with_media(self):
        """Test creator profile displays media correctly"""
        post = Post.objects.create(
            creator=self.creator,
            title='Test Post',
            text='Test content',
            visibility='public'
        )
        
        # Create test media
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        Media.objects.create(
            post=post,
            file=image,
            media_type='image'
        )
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(post, response.context['posts'])

    def test_creator_profile_subscription_status(self):
        """Test subscription status display for logged-in users"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Create an active subscription
        Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at='2024-12-31'
        )
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_subscriber'])

    def test_creator_profile_edit_buttons(self):
        """Test edit buttons visibility for creator"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Profile')
        self.assertContains(response, 'Create Post')

    def test_creator_profile_edit_buttons_not_visible(self):
        """Test edit buttons not visible for non-creator"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Edit Profile')
        self.assertNotContains(response, 'Create Post')

    def test_creator_profile_premium_content(self):
        """Test premium content visibility"""
        post = Post.objects.create(
            creator=self.creator,
            title='Premium Post',
            text='Premium content',
            visibility='premium',
            price=10.00
        )
        
        # Test as non-subscriber
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Premium')
        self.assertContains(response, 'Subscribe for')

        # Test as subscriber
        self.client.login(username='subscriber', password='testpass123')
        Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at='2024-12-31'
        )
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Purchase for $10.00')

    def test_creator_profile_stats(self):
        """Test creator profile statistics"""
        # Create some posts
        for i in range(3):
            Post.objects.create(
                creator=self.creator,
                title=f'Post {i}',
                text='Test content',
                visibility='public'
            )
        
        # Create some subscribers
        for i in range(2):
            subscriber = User.objects.create_user(
                username=f'subscriber{i}',
                email=f'subscriber{i}@example.com',
                password='testpass123'
            )
            Subscription.objects.create(
                subscriber=subscriber,
                creator=self.creator,
                active=True,
                expires_at='2024-12-31'
            )
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts_count'], 3)
        self.assertEqual(response.context['subscribers_count'], 2)

    def test_creator_profile_cover_photo(self):
        """Test cover photo display"""
        # Create a test cover photo
        cover_photo = SimpleUploadedFile(
            name='cover.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        self.creator.profile.cover_photo = cover_photo
        self.creator.profile.save()
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cover_photo')

    def test_creator_profile_bio(self):
        """Test bio display"""
        self.creator.profile.bio = 'Test bio'
        self.creator.profile.save()
        
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test bio')

    def test_creator_profile_no_posts(self):
        """Test profile display when creator has no posts"""
        response = self.client.get(self.creator_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No posts yet from this creator') 