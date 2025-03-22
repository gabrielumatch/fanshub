from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

class PostTests(TestCase):
    def setUp(self):
        # Create test users
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
        self.non_subscriber = User.objects.create_user(
            username='nonsubscriber',
            email='nonsubscriber@example.com',
            password='testpass123'
        )

        # Create an active subscription
        self.subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at=timezone.now() + timedelta(days=30),
            price=9.99
        )

        # Create test image
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',  # Add some image bytes in a real test
            content_type='image/jpeg'
        )

        self.client = Client()

    def test_create_public_post(self):
        """Test creating a public post"""
        self.client.login(username='creator', password='testpass123')
        
        response = self.client.post(reverse('create_post'), {
            'title': 'Test Public Post',
            'text': 'This is a test public post',
            'visibility': 'public',
            'media': [self.test_image]
        })

        self.assertEqual(response.status_code, 302)  # Should redirect after creation
        
        # Verify post was created
        post = Post.objects.get(title='Test Public Post')
        self.assertEqual(post.creator, self.creator)
        self.assertEqual(post.visibility, 'public')
        self.assertEqual(post.text, 'This is a test public post')

        # Verify media was attached
        self.assertEqual(post.media.count(), 1)
        self.assertEqual(post.media.first().media_type, 'image')

    def test_create_subscribers_only_post(self):
        """Test creating a subscribers-only post"""
        self.client.login(username='creator', password='testpass123')
        
        response = self.client.post(reverse('create_post'), {
            'title': 'Test Subscribers Post',
            'text': 'This is a test subscribers-only post',
            'visibility': 'subscribers',
            'media': [self.test_image]
        })

        self.assertEqual(response.status_code, 302)
        
        post = Post.objects.get(title='Test Subscribers Post')
        self.assertEqual(post.visibility, 'subscribers')

        # Test visibility for different users
        self.client.logout()

        # Subscriber should see the post
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('view_post', args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is a test subscribers-only post')

        # Non-subscriber should not see the post content
        self.client.logout()
        self.client.login(username='nonsubscriber', password='testpass123')
        response = self.client.get(reverse('view_post', args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'This is a test subscribers-only post')
        self.assertContains(response, 'Subscribe for')

    def test_create_premium_post(self):
        """Test creating a premium post"""
        self.client.login(username='creator', password='testpass123')
        
        response = self.client.post(reverse('create_post'), {
            'title': 'Test Premium Post',
            'text': 'This is a test premium post',
            'visibility': 'premium',
            'price': '4.99',
            'media': [self.test_image]
        })

        self.assertEqual(response.status_code, 302)
        
        post = Post.objects.get(title='Test Premium Post')
        self.assertEqual(post.visibility, 'premium')
        self.assertEqual(float(post.price), 4.99)

    def test_edit_post(self):
        """Test editing a post"""
        # Create a post first
        post = Post.objects.create(
            creator=self.creator,
            title='Original Title',
            text='Original text',
            visibility='public'
        )

        self.client.login(username='creator', password='testpass123')
        
        # Edit the post
        response = self.client.post(
            reverse('edit_post', args=[post.id]),
            {
                'title': 'Updated Title',
                'text': 'Updated text',
                'visibility': 'subscribers'
            }
        )

        self.assertEqual(response.status_code, 302)
        
        # Verify changes
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Title')
        self.assertEqual(post.text, 'Updated text')
        self.assertEqual(post.visibility, 'subscribers')

    def test_delete_post(self):
        """Test deleting a post"""
        post = Post.objects.create(
            creator=self.creator,
            title='Post to Delete',
            text='This post will be deleted',
            visibility='public'
        )

        self.client.login(username='creator', password='testpass123')
        
        response = self.client.post(reverse('delete_post', args=[post.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify post was deleted
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post.id)

    def test_unauthorized_post_creation(self):
        """Test that non-creators cannot create posts"""
        self.client.login(username='subscriber', password='testpass123')
        
        response = self.client.post(reverse('create_post'), {
            'title': 'Unauthorized Post',
            'text': 'This should not be created',
            'visibility': 'public'
        })

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Post.objects.filter(title='Unauthorized Post').count(), 0)

    def test_post_validation(self):
        """Test post validation rules"""
        self.client.login(username='creator', password='testpass123')
        
        # Test missing required fields
        response = self.client.post(reverse('create_post'), {
            'title': '',  # Missing title
            'text': 'Some text',
            'visibility': 'public'
        })
        self.assertEqual(response.status_code, 400)

        # Test invalid visibility choice
        response = self.client.post(reverse('create_post'), {
            'title': 'Test Post',
            'text': 'Some text',
            'visibility': 'invalid_choice'  # Invalid visibility
        })
        self.assertEqual(response.status_code, 400)

        # Test premium post without price
        response = self.client.post(reverse('create_post'), {
            'title': 'Premium Post',
            'text': 'Premium content',
            'visibility': 'premium'  # Missing price for premium post
        })
        self.assertEqual(response.status_code, 400)

    def test_post_media_handling(self):
        """Test handling of post media attachments"""
        self.client.login(username='creator', password='testpass123')
        
        # Create post with multiple media files
        image1 = SimpleUploadedFile(
            'image1.jpg',
            b'',
            content_type='image/jpeg'
        )
        image2 = SimpleUploadedFile(
            'image2.jpg',
            b'',
            content_type='image/jpeg'
        )

        response = self.client.post(reverse('create_post'), {
            'title': 'Multi-Media Post',
            'text': 'Post with multiple images',
            'visibility': 'public',
            'media': [image1, image2]
        })

        self.assertEqual(response.status_code, 302)
        
        post = Post.objects.get(title='Multi-Media Post')
        self.assertEqual(post.media.count(), 2)

        # Test media deletion
        media_id = post.media.first().id
        response = self.client.post(reverse('delete_media', args=[media_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.media.count(), 1) 