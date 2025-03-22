from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from notifications.models import Notification
from content.models import Post, Comment, Like
from subscriptions.models import Subscription

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
        """Test notification when new subscriber follows"""
        subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_subscriber'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertEqual(notification.target, subscription)

    def test_new_comment_notification(self):
        """Test notification when new comment is made"""
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        )
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_comment'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertEqual(notification.target, comment)

    def test_new_like_notification(self):
        """Test notification when post is liked"""
        like = Like.objects.create(
            user=self.subscriber,
            post=self.post
        )
        notification = Notification.objects.get(
            recipient=self.creator,
            notification_type='new_like'
        )
        self.assertEqual(notification.actor, self.subscriber)
        self.assertEqual(notification.target, like)

    def test_subscription_renewal_notification(self):
        """Test notification for subscription renewal"""
        subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        # Simulate subscription renewal
        subscription.renew()
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='subscription_renewed'
        )
        self.assertEqual(notification.actor, self.creator)
        self.assertEqual(notification.target, subscription)

    def test_payment_failure_notification(self):
        """Test notification for failed payment"""
        subscription = Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        # Simulate payment failure
        subscription.handle_payment_failure()
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='payment_failed'
        )
        self.assertEqual(notification.actor, self.creator)
        self.assertEqual(notification.target, subscription)

    def test_content_approval_notification(self):
        """Test notification for content approval"""
        post = Post.objects.create(
            creator=self.subscriber,
            title='Pending Post',
            text='Test content',
            visibility='public',
            status='pending'
        )
        # Simulate content approval
        post.approve()
        notification = Notification.objects.get(
            recipient=self.subscriber,
            notification_type='content_approved'
        )
        self.assertEqual(notification.target, post)

    def test_notification_read_status(self):
        """Test marking notifications as read"""
        # Create a notification
        notification = Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_subscriber',
            target=self.post
        )
        # Mark as read
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('mark_notification_read', kwargs={'notification_id': notification.id})
        )
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.read)

    def test_notification_list_view(self):
        """Test notification list view"""
        # Create some notifications
        for i in range(3):
            Notification.objects.create(
                recipient=self.creator,
                actor=self.subscriber,
                notification_type='new_like',
                target=self.post
            )
        # Test view
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 3)

    def test_notification_preferences(self):
        """Test notification preferences"""
        self.client.login(username='creator', password='testpass123')
        # Update preferences
        response = self.client.post(
            reverse('notification_preferences'),
            {
                'email_notifications': True,
                'push_notifications': False,
                'new_subscriber_notifications': True,
                'new_comment_notifications': False,
                'new_like_notifications': True
            }
        )
        self.assertEqual(response.status_code, 200)
        # Verify preferences were saved
        self.creator.refresh_from_db()
        self.assertTrue(self.creator.profile.email_notifications)
        self.assertFalse(self.creator.profile.push_notifications)

    def test_notification_cleanup(self):
        """Test cleanup of old notifications"""
        # Create old notification
        old_notification = Notification.objects.create(
            recipient=self.creator,
            actor=self.subscriber,
            notification_type='new_like',
            target=self.post,
            created_at=timezone.now() - timezone.timedelta(days=90)
        )
        # Run cleanup
        Notification.cleanup_old_notifications()
        # Verify old notification was deleted
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())

    def test_notification_batch_actions(self):
        """Test batch actions on notifications"""
        # Create multiple notifications
        notifications = []
        for i in range(3):
            notification = Notification.objects.create(
                recipient=self.creator,
                actor=self.subscriber,
                notification_type='new_like',
                target=self.post
            )
            notifications.append(notification)
        
        # Test marking all as read
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('mark_all_notifications_read'),
            {'notification_ids': [n.id for n in notifications]}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify all notifications are read
        for notification in notifications:
            notification.refresh_from_db()
            self.assertTrue(notification.read) 