from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Comment, Like
from django.utils import timezone

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
        response = self.client.post(
            reverse('like_post', kwargs={'post_id': self.post.id}),
            {'action': 'like'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_unlike_post(self):
        """Test unliking a post"""
        self.client.login(username='subscriber', password='testpass123')
        # First like the post
        Like.objects.create(user=self.subscriber, post=self.post)
        # Then unlike it
        response = self.client.post(
            reverse('like_post', kwargs={'post_id': self.post.id}),
            {'action': 'unlike'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(user=self.subscriber, post=self.post).exists())

    def test_add_comment(self):
        """Test adding a comment to a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Test comment'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        ).exists())

    def test_delete_comment(self):
        """Test deleting a comment"""
        self.client.login(username='subscriber', password='testpass123')
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Test comment'
        )
        response = self.client.post(
            reverse('delete_comment', kwargs={'comment_id': comment.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_edit_comment(self):
        """Test editing a comment"""
        self.client.login(username='subscriber', password='testpass123')
        comment = Comment.objects.create(
            user=self.subscriber,
            post=self.post,
            content='Original comment'
        )
        response = self.client.post(
            reverse('edit_comment', kwargs={'comment_id': comment.id}),
            {'content': 'Updated comment'}
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment')

    def test_report_content(self):
        """Test reporting content"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('report_content', kwargs={'post_id': self.post.id}),
            {
                'reason': 'inappropriate',
                'description': 'Test report'
            }
        )
        self.assertEqual(response.status_code, 200)
        # Verify report was created (assuming you have a Report model)

    def test_follow_creator(self):
        """Test following a creator"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('follow_creator', kwargs={'username': self.creator.username}),
            {'action': 'follow'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.subscriber.following.filter(id=self.creator.id).exists())

    def test_unfollow_creator(self):
        """Test unfollowing a creator"""
        self.client.login(username='subscriber', password='testpass123')
        # First follow the creator
        self.subscriber.following.add(self.creator)
        # Then unfollow
        response = self.client.post(
            reverse('follow_creator', kwargs={'username': self.creator.username}),
            {'action': 'unfollow'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.subscriber.following.filter(id=self.creator.id).exists())

    def test_save_post(self):
        """Test saving a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('save_post', kwargs={'post_id': self.post.id}),
            {'action': 'save'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.subscriber.saved_posts.filter(id=self.post.id).exists())

    def test_unsave_post(self):
        """Test unsaving a post"""
        self.client.login(username='subscriber', password='testpass123')
        # First save the post
        self.subscriber.saved_posts.add(self.post)
        # Then unsave
        response = self.client.post(
            reverse('save_post', kwargs={'post_id': self.post.id}),
            {'action': 'unsave'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.subscriber.saved_posts.filter(id=self.post.id).exists())

    def test_share_post(self):
        """Test sharing a post"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.post(
            reverse('share_post', kwargs={'post_id': self.post.id}),
            {
                'platform': 'twitter',
                'message': 'Check out this post!'
            }
        )
        self.assertEqual(response.status_code, 200)
        # Verify share was recorded (assuming you have a Share model)

    def test_comment_permissions(self):
        """Test comment permissions"""
        # Test unauthenticated user cannot comment
        response = self.client.post(
            reverse('add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Test comment'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test user cannot edit other user's comment
        self.client.login(username='subscriber', password='testpass123')
        other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123'
        )
        comment = Comment.objects.create(
            user=other_user,
            post=self.post,
            content='Other user comment'
        )
        response = self.client.post(
            reverse('edit_comment', kwargs={'comment_id': comment.id}),
            {'content': 'Updated comment'}
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_like_permissions(self):
        """Test like permissions"""
        # Test unauthenticated user cannot like
        response = self.client.post(
            reverse('like_post', kwargs={'post_id': self.post.id}),
            {'action': 'like'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test user cannot like their own post
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('like_post', kwargs={'post_id': self.post.id}),
            {'action': 'like'}
        )
        self.assertEqual(response.status_code, 400)  # Bad request 