from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
import os

User = get_user_model()

class MediaTests(TestCase):
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
        
        # Create test media files
        self.image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        self.video_content = b'RIFF....AVI LIST'
        self.audio_content = b'ID3\x03\x00\x00\x00\x00\x00\x0f'
        
        self.image_file = SimpleUploadedFile(
            'test_image.gif',
            self.image_content,
            content_type='image/gif'
        )
        self.video_file = SimpleUploadedFile(
            'test_video.avi',
            self.video_content,
            content_type='video/x-msvideo'
        )
        self.audio_file = SimpleUploadedFile(
            'test_audio.mp3',
            self.audio_content,
            content_type='audio/mpeg'
        )

    def test_upload_image(self):
        """Test uploading an image to a post"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': self.image_file, 'media_type': 'image'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Media.objects.filter(post=self.post, media_type='image').exists())

    def test_upload_video(self):
        """Test uploading a video to a post"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': self.video_file, 'media_type': 'video'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Media.objects.filter(post=self.post, media_type='video').exists())

    def test_upload_audio(self):
        """Test uploading an audio file to a post"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': self.audio_file, 'media_type': 'audio'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Media.objects.filter(post=self.post, media_type='audio').exists())

    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type"""
        self.client.login(username='creator', password='testpass123')
        invalid_file = SimpleUploadedFile(
            'test.exe',
            b'Invalid content',
            content_type='application/x-msdownload'
        )
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': invalid_file, 'media_type': 'image'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Media.objects.filter(post=self.post).exists())

    def test_upload_file_size_limit(self):
        """Test uploading a file that exceeds size limit"""
        self.client.login(username='creator', password='testpass123')
        large_file = SimpleUploadedFile(
            'large_image.jpg',
            b'x' * (10 * 1024 * 1024 + 1),  # 10MB + 1 byte
            content_type='image/jpeg'
        )
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': large_file, 'media_type': 'image'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Media.objects.filter(post=self.post).exists())

    def test_delete_media(self):
        """Test deleting media from a post"""
        self.client.login(username='creator', password='testpass123')
        media = Media.objects.create(
            post=self.post,
            media_type='image',
            file=self.image_file
        )
        response = self.client.delete(
            reverse('content:delete_media', args=[media.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Media.objects.filter(id=media.id).exists())

    def test_media_permissions(self):
        """Test media access permissions"""
        # Create private post with media
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        media = Media.objects.create(
            post=private_post,
            media_type='image',
            file=self.image_file
        )
        
        # Test unauthorized access
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(
            reverse('content:media_detail', args=[media.id])
        )
        self.assertEqual(response.status_code, 403)
        
        # Test authorized access
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('content:media_detail', args=[media.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_media_processing(self):
        """Test media processing (compression, resizing)"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': self.image_file, 'media_type': 'image'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        
        media = Media.objects.get(post=self.post, media_type='image')
        # Verify processed file exists
        self.assertTrue(os.path.exists(media.file.path))
        # Verify thumbnail exists
        self.assertTrue(os.path.exists(media.thumbnail.path))

    def test_media_ordering(self):
        """Test media ordering within a post"""
        self.client.login(username='creator', password='testpass123')
        
        # Create multiple media items
        media1 = Media.objects.create(
            post=self.post,
            media_type='image',
            file=self.image_file,
            order=2
        )
        media2 = Media.objects.create(
            post=self.post,
            media_type='image',
            file=self.image_file,
            order=1
        )
        
        # Test reordering
        response = self.client.post(
            reverse('content:reorder_media', args=[self.post.id]),
            {'media_ids': [media2.id, media1.id]},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify new order
        media1.refresh_from_db()
        media2.refresh_from_db()
        self.assertEqual(media1.order, 2)
        self.assertEqual(media2.order, 1)

    def test_media_metadata(self):
        """Test media metadata extraction"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('content:add_media', args=[self.post.id]),
            {'media': self.image_file, 'media_type': 'image'},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        
        media = Media.objects.get(post=self.post, media_type='image')
        # Verify metadata
        self.assertIsNotNone(media.width)
        self.assertIsNotNone(media.height)
        self.assertIsNotNone(media.duration)  # For video/audio
        self.assertIsNotNone(media.file_size) 