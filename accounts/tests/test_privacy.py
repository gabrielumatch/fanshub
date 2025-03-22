from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from content.models import Post, BlockedContent, BlockedUser
from django.utils import timezone
from datetime import timedelta

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

    def test_block_content(self):
        """Test blocking content"""
        self.client.login(username='subscriber', password='testpass123')
        
        response = self.client.post(
            reverse('accounts:block_content', args=[self.post.id]),
            {'reason': 'inappropriate'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BlockedContent.objects.filter(
            user=self.subscriber,
            content=self.post
        ).exists())

    def test_block_user(self):
        """Test blocking a user"""
        self.client.login(username='subscriber', password='testpass123')
        
        response = self.client.post(
            reverse('accounts:block_user', args=[self.creator.id]),
            {'reason': 'harassment'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BlockedUser.objects.filter(
            blocker=self.subscriber,
            blocked=self.creator
        ).exists())

    def test_report_content(self):
        """Test reporting content"""
        self.client.login(username='subscriber', password='testpass123')
        
        response = self.client.post(
            reverse('accounts:report_content', args=[self.post.id]),
            {
                'reason': 'inappropriate',
                'description': 'Contains offensive material'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.post.reports.filter(
            reporter=self.subscriber,
            reason='inappropriate'
        ).exists())

    def test_content_moderation(self):
        """Test content moderation"""
        # Create moderator
        moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Report content
        self.post.reports.create(
            reporter=self.subscriber,
            reason='inappropriate'
        )
        
        # Moderate content
        self.client.login(username='moderator', password='testpass123')
        response = self.client.post(
            reverse('accounts:moderate_content', args=[self.post.id]),
            {
                'action': 'remove',
                'reason': 'Violates community guidelines'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'removed')

    def test_privacy_settings(self):
        """Test privacy settings management"""
        self.client.login(username='creator', password='testpass123')
        
        response = self.client.post(
            reverse('accounts:privacy_settings'),
            {
                'profile_visibility': 'private',
                'show_online_status': False,
                'allow_messages': False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.creator.refresh_from_db()
        self.assertEqual(self.creator.profile_visibility, 'private')
        self.assertFalse(self.creator.show_online_status)
        self.assertFalse(self.creator.allow_messages)

    def test_two_factor_authentication(self):
        """Test two-factor authentication"""
        self.client.login(username='creator', password='testpass123')
        
        # Enable 2FA
        response = self.client.post(
            reverse('accounts:enable_2fa'),
            {'phone_number': '+1234567890'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.creator.refresh_from_db()
        self.assertTrue(self.creator.two_factor_enabled)
        
        # Disable 2FA
        response = self.client.post(reverse('accounts:disable_2fa'))
        
        self.assertEqual(response.status_code, 200)
        self.creator.refresh_from_db()
        self.assertFalse(self.creator.two_factor_enabled)

    def test_session_management(self):
        """Test session management"""
        self.client.login(username='creator', password='testpass123')
        
        # Create multiple sessions
        self.client.get(reverse('home'))
        self.client.get(reverse('profile'))
        
        # View active sessions
        response = self.client.get(reverse('accounts:active_sessions'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['sessions']), 2)
        
        # Terminate session
        response = self.client.post(
            reverse('accounts:terminate_session'),
            {'session_id': response.json()['sessions'][0]['id']}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['sessions']), 1)

    def test_ip_blocking(self):
        """Test IP blocking"""
        # Create blocked IP
        response = self.client.post(
            reverse('accounts:block_ip'),
            {
                'ip_address': '192.168.1.1',
                'reason': 'suspicious_activity'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BlockedIP.objects.filter(
            ip_address='192.168.1.1'
        ).exists())

    def test_content_visibility_rules(self):
        """Test content visibility rules"""
        # Create private post
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        
        # Test unauthorized access
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(
            reverse('content:post_detail', args=[private_post.id])
        )
        
        self.assertEqual(response.status_code, 403)
        
        # Test authorized access
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('content:post_detail', args=[private_post.id])
        )
        
        self.assertEqual(response.status_code, 200)

    def test_data_privacy_compliance(self):
        """Test data privacy compliance"""
        self.client.login(username='creator', password='testpass123')
        
        # Request data export
        response = self.client.post(reverse('accounts:export_data'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
        
        # Request account deletion
        response = self.client.post(
            reverse('accounts:delete_account'),
            {'confirmation': 'DELETE'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.creator.id).exists())

    def test_password_security(self):
        """Test password security features"""
        self.client.login(username='creator', password='testpass123')
        
        # Test password change
        response = self.client.post(
            reverse('accounts:change_password'),
            {
                'old_password': 'testpass123',
                'new_password': 'newpass123',
                'confirm_password': 'newpass123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Test password requirements
        response = self.client.post(
            reverse('accounts:change_password'),
            {
                'old_password': 'newpass123',
                'new_password': 'weak',
                'confirm_password': 'weak'
            }
        )
        
        self.assertEqual(response.status_code, 400) 