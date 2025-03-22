from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Report
from django.utils import timezone

User = get_user_model()

class PrivacyAndSecurityTests(TestCase):
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

    def test_content_blocking(self):
        """Test blocking content"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('block_content', kwargs={'post_id': self.post.id}),
            {'reason': 'inappropriate'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.subscriber.blocked_content.filter(id=self.post.id).exists())

    def test_user_blocking(self):
        """Test blocking users"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('block_user', kwargs={'username': self.creator.username}),
            {'reason': 'harassment'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.subscriber.blocked_users.filter(id=self.creator.id).exists())

    def test_report_handling(self):
        """Test content reporting"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('report_content', kwargs={'post_id': self.post.id}),
            {
                'reason': 'inappropriate',
                'description': 'Test report'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Report.objects.filter(
            reporter=self.subscriber,
            content=self.post,
            reason='inappropriate'
        ).exists())

    def test_content_moderation(self):
        """Test content moderation"""
        # Create a post that needs moderation
        post = Post.objects.create(
            creator=self.subscriber,
            title='Pending Post',
            text='Test content',
            visibility='public',
            status='pending'
        )
        
        # Login as moderator
        moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='moderator', password='testpass123')
        
        # Approve post
        response = self.client.post(
            reverse('moderate_content', kwargs={'post_id': post.id}),
            {'action': 'approve'}
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, 'approved')
        
        # Reject post
        post.status = 'pending'
        post.save()
        response = self.client.post(
            reverse('moderate_content', kwargs={'post_id': post.id}),
            {
                'action': 'reject',
                'reason': 'inappropriate content'
            }
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, 'rejected')

    def test_privacy_settings(self):
        """Test privacy settings management"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('privacy_settings'),
            {
                'profile_visibility': 'public',
                'show_online_status': True,
                'allow_messages': True,
                'show_subscriber_count': True
            }
        )
        self.assertEqual(response.status_code, 200)
        self.creator.profile.refresh_from_db()
        self.assertEqual(self.creator.profile.profile_visibility, 'public')
        self.assertTrue(self.creator.profile.show_online_status)
        self.assertTrue(self.creator.profile.allow_messages)
        self.assertTrue(self.creator.profile.show_subscriber_count)

    def test_two_factor_authentication(self):
        """Test two-factor authentication"""
        self.client.login(username='creator', password='testpass123')
        # Enable 2FA
        response = self.client.post(
            reverse('enable_2fa'),
            {'method': 'authenticator'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.creator.profile.two_factor_enabled)
        
        # Disable 2FA
        response = self.client.post(
            reverse('disable_2fa'),
            {'code': '123456'}  # Mock code
        )
        self.assertEqual(response.status_code, 200)
        self.creator.profile.refresh_from_db()
        self.assertFalse(self.creator.profile.two_factor_enabled)

    def test_session_management(self):
        """Test session management"""
        self.client.login(username='creator', password='testpass123')
        # Get active sessions
        response = self.client.get(reverse('active_sessions'))
        self.assertEqual(response.status_code, 200)
        
        # Terminate session
        response = self.client.post(
            reverse('terminate_session'),
            {'session_id': 'test_session_id'}
        )
        self.assertEqual(response.status_code, 200)

    def test_ip_blocking(self):
        """Test IP blocking"""
        # Login as moderator
        moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='moderator', password='testpass123')
        
        # Block IP
        response = self.client.post(
            reverse('block_ip'),
            {
                'ip_address': '192.168.1.1',
                'reason': 'suspicious activity',
                'duration': '24h'
            }
        )
        self.assertEqual(response.status_code, 200)
        
        # Try to access with blocked IP
        self.client.logout()
        self.client.META['REMOTE_ADDR'] = '192.168.1.1'
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 403)

    def test_content_visibility_rules(self):
        """Test content visibility rules"""
        # Create posts with different visibility settings
        public_post = Post.objects.create(
            creator=self.creator,
            title='Public Post',
            text='Public content',
            visibility='public'
        )
        
        subscriber_post = Post.objects.create(
            creator=self.creator,
            title='Subscriber Post',
            text='Subscriber content',
            visibility='subscribers'
        )
        
        premium_post = Post.objects.create(
            creator=self.creator,
            title='Premium Post',
            text='Premium content',
            visibility='premium',
            price=10.00
        )
        
        # Test as non-subscriber
        self.client.logout()
        response = self.client.get(reverse('post_detail', kwargs={'post_id': public_post.id}))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('post_detail', kwargs={'post_id': subscriber_post.id}))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('post_detail', kwargs={'post_id': premium_post.id}))
        self.assertEqual(response.status_code, 403)
        
        # Test as subscriber
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', kwargs={'post_id': subscriber_post.id}))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('post_detail', kwargs={'post_id': premium_post.id}))
        self.assertEqual(response.status_code, 403)

    def test_data_privacy(self):
        """Test data privacy compliance"""
        self.client.login(username='creator', password='testpass123')
        # Request data export
        response = self.client.post(reverse('request_data_export'))
        self.assertEqual(response.status_code, 200)
        
        # Delete account
        response = self.client.post(
            reverse('delete_account'),
            {'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='creator').exists()) 