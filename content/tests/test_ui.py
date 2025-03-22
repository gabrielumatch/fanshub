from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
from django.utils import timezone

User = get_user_model()

class UITests(TestCase):
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

    def test_creator_profile_ui(self):
        """Test creator profile page UI elements"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('creator_profile', kwargs={'username': self.creator.username}))
        self.assertEqual(response.status_code, 200)
        
        # Check profile header elements
        self.assertContains(response, self.creator.username)
        self.assertContains(response, 'Subscribe')
        self.assertContains(response, 'Creator Stats')
        
        # Check profile picture display
        if self.creator.profile_picture:
            self.assertContains(response, self.creator.profile_picture.url)
        else:
            self.assertContains(response, 'default-profile.png')
        
        # Check cover photo display
        if self.creator.cover_photo:
            self.assertContains(response, self.creator.cover_photo.url)
        else:
            self.assertContains(response, 'default-cover.jpg')

    def test_post_detail_ui(self):
        """Test post detail page UI elements"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        
        # Check post header elements
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.text)
        self.assertContains(response, self.creator.username)
        
        # Check post actions
        self.assertContains(response, 'like')
        self.assertContains(response, 'comment')
        
        # Check edit/delete buttons for creator
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('post_detail', kwargs={'post_id': self.post.id}))
        self.assertContains(response, 'Edit')
        self.assertContains(response, 'Delete')

    def test_landing_page_ui(self):
        """Test landing page UI elements"""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        
        # Check hero section
        self.assertContains(response, 'Connect with your favorite creators')
        self.assertContains(response, 'Join Now')
        self.assertContains(response, 'Discover Creators')
        
        # Check featured creators section
        self.assertContains(response, 'Featured Creators')
        
        # Check why join section
        self.assertContains(response, 'Why join FansHub?')
        self.assertContains(response, 'Support Creators')
        self.assertContains(response, 'Exclusive Content')
        self.assertContains(response, 'Direct Connection')

    def test_subscription_management_ui(self):
        """Test subscription management page UI elements"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('subscriptions:manage_subscriptions'))
        self.assertEqual(response.status_code, 200)
        
        # Check subscription sections
        self.assertContains(response, 'Active Subscriptions')
        self.assertContains(response, 'Past Subscriptions')
        
        # Check subscription management buttons
        self.assertContains(response, 'Cancel Subscription')
        self.assertContains(response, 'Update Payment Method')

    def test_navigation_ui(self):
        """Test navigation elements"""
        # Test navigation for non-authenticated users
        response = self.client.get(reverse('landing'))
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'My Profile')
        
        # Test navigation for authenticated users
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('landing'))
        self.assertContains(response, 'My Profile')
        self.assertContains(response, 'Settings')
        self.assertContains(response, 'Payment Methods')
        self.assertContains(response, 'Logout')

    def test_media_handling_ui(self):
        """Test media handling in posts"""
        # Create a post with media
        media_file = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        media = Media.objects.create(
            post=self.post,
            file=media_file,
            media_type='image'
        )
        
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        
        # Check media display
        self.assertContains(response, media.file.url)
        self.assertContains(response, 'post-media')
        
        # Test media fallback
        self.assertContains(response, 'data-fallback')

    def test_responsive_design(self):
        """Test responsive design elements"""
        # Test mobile viewport meta tag
        response = self.client.get(reverse('landing'))
        self.assertContains(response, 'width=device-width')
        self.assertContains(response, 'initial-scale=1.0')
        
        # Test responsive classes
        self.assertContains(response, 'col-md-')
        self.assertContains(response, 'col-lg-')
        self.assertContains(response, 'container-fluid')

    def test_error_handling_ui(self):
        """Test error handling UI elements"""
        # Test 404 page
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        
        # Test 403 page
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('creator_dashboard'))
        self.assertEqual(response.status_code, 403)
        
        # Test 500 page (simulated)
        with self.settings(DEBUG=False):
            response = self.client.get('/trigger-500/')
            self.assertEqual(response.status_code, 500)

    def test_loading_states(self):
        """Test loading states and transitions"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        
        # Check loading indicators
        self.assertContains(response, 'loading')
        self.assertContains(response, 'spinner')
        
        # Check transition classes
        self.assertContains(response, 'fade')
        self.assertContains(response, 'transition') 