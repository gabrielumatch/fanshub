from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from content.models import Post, Comment, Like, Share, Save
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SocialFeaturesTests(TestCase):
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

    def test_like_post(self):
        """Test liking a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_unlike_post(self):
        """Test unliking a post"""
        self.client.login(username='subscriber', password='testpass123')
        # First like the post
        Like.objects.create(user=self.subscriber, post=self.post)
        # Then unlike it
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_like_private_post(self):
        """Test liking a private post"""
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('like_post', args=[private_post.id]))
        self.assertEqual(response.status_code, 403)

    def test_add_comment(self):
        """Test adding a comment"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('add_comment', args=[self.post.id]), {
            'content': 'Test comment'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        ).exists())

    def test_edit_comment(self):
        """Test editing a comment"""
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Original comment'
        )
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('edit_comment', args=[comment.id]), {
            'content': 'Updated comment'
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment')

    def test_delete_comment(self):
        """Test deleting a comment"""
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        )
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('delete_comment', args=[comment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_share_post(self):
        """Test sharing a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('share_post', args=[self.post.id]), {
            'platform': 'twitter',
            'message': 'Check out this post!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Share.objects.filter(
            user=self.subscriber,
            post=self.post,
            platform='twitter'
        ).exists())

    def test_save_post(self):
        """Test saving a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('save_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Save.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_unsave_post(self):
        """Test unsaving a post"""
        self.client.login(username='subscriber', password='testpass123')
        # First save the post
        Save.objects.create(user=self.subscriber, post=self.post)
        # Then unsave it
        response = self.client.post(reverse('save_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Save.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_report_post(self):
        """Test reporting a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('report_post', args=[self.post.id]), {
            'reason': 'inappropriate_content',
            'description': 'This post contains inappropriate content'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.post.reports.filter(
            reporter=self.subscriber,
            reason='inappropriate_content'
        ).exists())

    def test_follow_creator(self):
        """Test following a creator"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('follow_creator', args=[self.creator.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.subscriber.following.filter(id=self.creator.id).exists())

    def test_unfollow_creator(self):
        """Test unfollowing a creator"""
        self.client.login(username='subscriber', password='testpass123')
        # First follow the creator
        self.subscriber.following.add(self.creator)
        # Then unfollow
        response = self.client.post(reverse('follow_creator', args=[self.creator.username]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.subscriber.following.filter(id=self.creator.id).exists())

    def test_comment_replies(self):
        """Test comment reply functionality"""
        parent_comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Parent comment'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(reverse('reply_to_comment', args=[parent_comment.id]), {
            'content': 'Reply to comment'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(
            user=self.creator,
            post=self.post,
            parent=parent_comment,
            content='Reply to comment'
        ).exists())

    def test_comment_likes(self):
        """Test liking comments"""
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(reverse('like_comment', args=[comment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(comment.likes.filter(user=self.creator).exists())

    def test_comment_mentions(self):
        """Test mentioning users in comments"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('add_comment', args=[self.post.id]), {
            'content': 'Hello @creator!'
        })
        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get(user=self.subscriber, post=self.post)
        self.assertTrue(comment.mentions.filter(username='creator').exists())

    def test_share_private_post(self):
        """Test sharing a private post"""
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('share_post', args=[private_post.id]), {
            'platform': 'twitter',
            'message': 'Check out this post!'
        })
        self.assertEqual(response.status_code, 403)

    def test_comment_on_private_post(self):
        """Test commenting on a private post"""
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(reverse('add_comment', args=[private_post.id]), {
            'content': 'Test comment'
        })
        self.assertEqual(response.status_code, 403)

    def test_comment_visibility(self):
        """Test comment visibility based on post visibility"""
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        # Create comment as creator
        self.client.login(username='creator', password='testpass123')
        self.client.post(reverse('add_comment', args=[private_post.id]), {
            'content': 'Creator comment'
        })
        # Try to view as subscriber
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('post_detail', args=[private_post.id]))
        self.assertEqual(response.status_code, 403) 