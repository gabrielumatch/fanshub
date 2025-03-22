from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from notifications.models import Notification
from content.models import Post
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class NotificationTests(TestCase):
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

    def test_new_subscriber_notification(self):
        """Test notification for new subscriber"""
        # Create subscription
        self.subscriber.subscriptions.create(
            creator=self.creator,
            status='active'
        )
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_subscriber'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertFalse(notification.read)

    def test_new_comment_notification(self):
        """Test notification for new comment"""
        # Create comment
        self.post.comments.create(
            user=self.subscriber,
            text='Test comment'
        )
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_comment'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertEqual(notification.target, self.post)
        self.assertFalse(notification.read)

    def test_new_like_notification(self):
        """Test notification for new like"""
        # Create like
        self.post.likes.create(user=self.subscriber)
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_like'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertEqual(notification.target, self.post)
        self.assertFalse(notification.read)

    def test_subscription_renewal_notification(self):
        """Test notification for subscription renewal"""
        # Create subscription
        subscription = self.subscriber.subscriptions.create(
            creator=self.creator,
            status='active'
        )
        
        # Simulate renewal
        subscription.renewal_date = timezone.now() + timedelta(days=1)
        subscription.save()
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='subscription_renewal'
        )
        self.assertEqual(notification.target, subscription)
        self.assertFalse(notification.read)

    def test_payment_failure_notification(self):
        """Test notification for payment failure"""
        # Create subscription
        subscription = self.subscriber.subscriptions.create(
            creator=self.creator,
            status='active'
        )
        
        # Simulate payment failure
        subscription.status = 'payment_failed'
        subscription.save()
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='payment_failure'
        )
        self.assertEqual(notification.target, subscription)
        self.assertFalse(notification.read)

    def test_content_approval_notification(self):
        """Test notification for content approval"""
        # Create pending post
        post = Post.objects.create(
            creator=self.subscriber,
            title='Pending Post',
            text='Pending content',
            status='pending'
        )
        
        # Approve post
        post.status = 'approved'
        post.save()
        
        # Check notification
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='content_approved'
        )
        self.assertEqual(notification.target, post)
        self.assertFalse(notification.read)

    def test_mark_notification_read(self):
        """Test marking notification as read"""
        # Create notification
        notification = Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber'
        )
        
        # Mark as read
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('notifications:mark_read', args=[notification.id])
        )
        
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.read)

    def test_notification_list(self):
        """Test listing notifications"""
        # Create multiple notifications
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber'
        )
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_comment',
            target=self.post
        )
        
        # Get notifications
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('notifications:list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['notifications']), 2)

    def test_notification_preferences(self):
        """Test notification preferences"""
        self.client.login(username='creator', password='testpass123')
        
        # Update preferences
        response = self.client.post(
            reverse('notifications:preferences'),
            {
                'email_notifications': False,
                'push_notifications': True,
                'notification_types': ['new_subscriber', 'new_comment']
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.creator.refresh_from_db()
        self.assertFalse(self.creator.email_notifications)
        self.assertTrue(self.creator.push_notifications)

    def test_cleanup_old_notifications(self):
        """Test cleanup of old notifications"""
        # Create old notification
        old_notification = Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber',
            created_at=timezone.now() - timedelta(days=90)
        )
        
        # Run cleanup
        Notification.cleanup_old_notifications()
        
        # Verify deletion
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())

    def test_batch_notification_actions(self):
        """Test batch actions on notifications"""
        # Create multiple notifications
        notifications = [
            Notification.objects.create(
                recipient=self.creator,
                actor=self.subscriber,
                notification_type='new_subscriber'
            ),
            Notification.objects.create(
                recipient=self.creator,
                actor=self.subscriber,
                notification_type='new_comment',
                target=self.post
            )
        ]
        
        # Mark all as read
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('notifications:mark_all_read'),
            {'notification_ids': [n.id for n in notifications]}
        )
        
        self.assertEqual(response.status_code, 200)
        for notification in notifications:
            notification.refresh_from_db()
            self.assertTrue(notification.read)

    def test_notification_count(self):
        """Test unread notification count"""
        # Create unread notifications
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber'
        )
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_comment',
            target=self.post
        )
        
        # Get count
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('notifications:count'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)

    def test_notification_filters(self):
        """Test filtering notifications"""
        # Create different types of notifications
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber'
        )
        Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_comment',
            target=self.post
        )
        
        # Filter by type
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('notifications:list'),
            {'type': 'new_subscriber'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['notifications']), 1) 