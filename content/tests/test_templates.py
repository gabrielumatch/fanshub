from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
from django.test.utils import override_settings
from django.core.cache import cache
from django.utils import translation
import json

User = get_user_model()

class TemplateTests(TestCase):
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

    def test_base_template_inheritance(self):
        """Test that all templates properly extend base.html"""
        templates = [
            'content/creator_profile.html',
            'content/post_detail.html',
            'content/landing.html',
            'content/subscription_management.html',
            'content/dashboard.html',
            'content/post_form.html',
            'content/media_upload.html',
            'content/analytics.html',
            'content/settings.html',
            'content/earnings.html',
            'content/subscribers.html',
            'content/content_management.html',
            'content/notifications.html',
            'content/search_results.html',
            'content/discover.html'
        ]
        
        for template in templates:
            try:
                rendered = render_to_string(template)
                self.assertIn('{% extends "base.html" %}', rendered)
            except Exception as e:
                self.fail(f"Template {template} failed to render: {str(e)}")

    def test_creator_profile_template(self):
        """Test creator profile template rendering"""
        response = self.client.get(reverse('creator_profile', args=[self.creator.username]))
        self.assertEqual(response.status_code, 200)
        
        # Check for required elements
        self.assertContains(response, self.creator.username)
        self.assertContains(response, 'Subscribe')
        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Followers')
        self.assertContains(response, 'Following')

    def test_post_detail_template(self):
        """Test post detail template rendering"""
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check for required elements
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.text)
        self.assertContains(response, 'Like')
        self.assertContains(response, 'Comment')
        self.assertContains(response, 'Share')

    def test_landing_page_template(self):
        """Test landing page template rendering"""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        
        # Check for required sections
        self.assertContains(response, 'Hero Section')
        self.assertContains(response, 'Featured Creators')
        self.assertContains(response, 'Popular Content')
        self.assertContains(response, 'Categories')

    def test_subscription_management_template(self):
        """Test subscription management template rendering"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('subscription_management'))
        self.assertEqual(response.status_code, 200)
        
        # Check for required elements
        self.assertContains(response, 'Active Subscriptions')
        self.assertContains(response, 'Payment Methods')
        self.assertContains(response, 'Billing History')

    def test_media_handling_in_templates(self):
        """Test media handling in templates"""
        # Create test media
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
        
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check for media elements
        self.assertContains(response, 'post-media')
        self.assertContains(response, 'media-preview')

    def test_error_handling_templates(self):
        """Test error handling templates"""
        # Test 404 template
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        
        # Test 500 template
        with self.settings(DEBUG=False):
            response = self.client.get('/trigger-500/')
            self.assertEqual(response.status_code, 500)
            self.assertTemplateUsed(response, '500.html')

    def test_message_display_in_templates(self):
        """Test message display in templates"""
        self.client.login(username='subscriber', password='testpass123')
        
        # Test success message
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertRedirects(response, reverse('post_detail', args=[self.post.id]))
        
        # Check for message in template
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertContains(response, 'Post liked successfully')

    def test_conditional_rendering(self):
        """Test conditional rendering in templates"""
        # Test creator-specific elements
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertContains(response, 'Edit Post')
        self.assertContains(response, 'Delete Post')
        
        # Test subscriber view
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertNotContains(response, 'Edit Post')
        self.assertNotContains(response, 'Delete Post')

    def test_static_file_handling(self):
        """Test static file handling in templates"""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        
        # Check for required static files
        self.assertContains(response, 'css/style.css')
        self.assertContains(response, 'js/main.js')
        self.assertContains(response, 'img/logo.png')

    def test_template_filters(self):
        """Test custom template filters"""
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check for formatted dates
        self.assertContains(response, self.post.created_at.strftime('%B %d, %Y'))
        
        # Check for formatted numbers
        self.assertContains(response, '0 likes')
        self.assertContains(response, '0 comments')

    def test_template_includes(self):
        """Test template includes"""
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check for included templates
        self.assertContains(response, '{% include "content/includes/post_actions.html" %}')
        self.assertContains(response, '{% include "content/includes/comment_list.html" %}')

    def test_template_context(self):
        """Test template context variables"""
        response = self.client.get(reverse('creator_profile', args=[self.creator.username]))
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertIn('creator', response.context)
        self.assertIn('posts', response.context)
        self.assertIn('subscriber_count', response.context)
        self.assertIn('is_subscribed', response.context)

    def test_template_inheritance_blocks(self):
        """Test template inheritance blocks"""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        
        # Check for block overrides
        self.assertContains(response, '{% block title %}')
        self.assertContains(response, '{% block content %}')
        self.assertContains(response, '{% block extra_js %}')

    def test_template_translations(self):
        """Test template translations"""
        # Test with English
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '{% trans "')
        self.assertContains(response, '{% blocktrans %}')
        
        # Test with Spanish
        with translation.override('es'):
            response = self.client.get(reverse('landing'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '{% trans "')
            self.assertContains(response, '{% blocktrans %}')

    def test_template_caching(self):
        """Test template caching"""
        # First request
        response1 = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response1.status_code, 200)
        
        # Update post
        self.post.title = 'Updated Title'
        self.post.save()
        
        # Second request should show cached version
        response2 = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, 'Updated Title')
        
        # Clear cache and verify update
        cache.clear()
        response3 = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response3.status_code, 200)
        self.assertContains(response3, 'Updated Title')

    def test_template_media_handling(self):
        """Test media handling in templates"""
        # Create test media
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
        
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check for media elements
        self.assertContains(response, 'post-media')
        self.assertContains(response, 'media-preview')
        
        # Test media fallback
        media.file.delete()
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'default-image.jpg')

    def test_template_conditional_visibility(self):
        """Test conditional visibility in templates"""
        # Test premium content visibility
        self.post.visibility = 'premium'
        self.post.save()
        
        # Test as non-subscriber
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'premium-content-blur')
        
        # Test as subscriber
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'premium-content-blur')

    def test_template_error_handling(self):
        """Test error handling in templates"""
        # Test missing template
        with self.assertRaises(Exception):
            render_to_string('nonexistent_template.html')
        
        # Test template syntax error
        with self.assertRaises(Exception):
            render_to_string('content/invalid_template.html')

    def test_template_performance(self):
        """Test template rendering performance"""
        # Create multiple posts
        for i in range(10):
            Post.objects.create(
                creator=self.creator,
                title=f'Test Post {i}',
                text=f'Test content {i}',
                visibility='public'
            )
        
        # Test rendering time
        import time
        start_time = time.time()
        response = self.client.get(reverse('creator_profile', args=[self.creator.username]))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should render in less than 1 second 