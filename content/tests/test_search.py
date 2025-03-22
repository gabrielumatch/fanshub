from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Category, Tag
from django.utils import timezone

User = get_user_model()

class SearchAndDiscoveryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123',
            is_creator=True
        )
        self.creator2 = User.objects.create_user(
            username='creator2',
            email='creator2@example.com',
            password='testpass123',
            is_creator=True
        )
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )
        
        # Create categories
        self.category1 = Category.objects.create(name='Photography')
        self.category2 = Category.objects.create(name='Art')
        
        # Create tags
        self.tag1 = Tag.objects.create(name='nature')
        self.tag2 = Tag.objects.create(name='portrait')
        
        # Create posts
        self.post1 = Post.objects.create(
            creator=self.creator,
            title='Nature Photography',
            text='Beautiful nature photos',
            visibility='public',
            category=self.category1
        )
        self.post1.tags.add(self.tag1)
        
        self.post2 = Post.objects.create(
            creator=self.creator2,
            title='Portrait Art',
            text='Amazing portraits',
            visibility='public',
            category=self.category2
        )
        self.post2.tags.add(self.tag2)

    def test_search_creators(self):
        """Test searching for creators"""
        response = self.client.get(
            reverse('search_creators'),
            {'q': 'creator'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['creators']), 2)
        self.assertIn(self.creator, response.context['creators'])
        self.assertIn(self.creator2, response.context['creators'])

    def test_search_content(self):
        """Test searching for content"""
        response = self.client.get(
            reverse('search_content'),
            {'q': 'photography'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertEqual(response.context['posts'][0], self.post1)

    def test_filter_by_category(self):
        """Test filtering content by category"""
        response = self.client.get(
            reverse('category_content', kwargs={'category_id': self.category1.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertEqual(response.context['posts'][0], self.post1)

    def test_filter_by_tag(self):
        """Test filtering content by tag"""
        response = self.client.get(
            reverse('tag_content', kwargs={'tag_id': self.tag1.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertEqual(response.context['posts'][0], self.post1)

    def test_sort_by_popularity(self):
        """Test sorting content by popularity"""
        # Add some likes to posts
        self.post2.likes.create(user=self.subscriber)
        self.post2.likes.create(user=self.creator)
        
        response = self.client.get(
            reverse('discover'),
            {'sort': 'popular'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts'][0], self.post2)

    def test_sort_by_date(self):
        """Test sorting content by date"""
        # Create a newer post
        newer_post = Post.objects.create(
            creator=self.creator,
            title='New Post',
            text='Latest content',
            visibility='public',
            created_at=timezone.now()
        )
        
        response = self.client.get(
            reverse('discover'),
            {'sort': 'newest'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts'][0], newer_post)

    def test_trending_creators(self):
        """Test trending creators section"""
        # Add some subscribers to creator2
        for i in range(3):
            subscriber = User.objects.create_user(
                username=f'subscriber{i}',
                email=f'subscriber{i}@example.com',
                password='testpass123'
            )
            self.creator2.subscribers.add(subscriber)
        
        response = self.client.get(reverse('trending_creators'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['creators'][0], self.creator2)

    def test_recommended_creators(self):
        """Test recommended creators for logged-in user"""
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('recommended_creators'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.creator, response.context['creators'])
        self.assertIn(self.creator2, response.context['creators'])

    def test_category_browsing(self):
        """Test browsing content by category"""
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['categories']), 2)
        self.assertIn(self.category1, response.context['categories'])
        self.assertIn(self.category2, response.context['categories'])

    def test_tag_browsing(self):
        """Test browsing content by tag"""
        response = self.client.get(reverse('tags'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tags']), 2)
        self.assertIn(self.tag1, response.context['tags'])
        self.assertIn(self.tag2, response.context['tags'])

    def test_search_with_multiple_criteria(self):
        """Test search with multiple criteria"""
        response = self.client.get(
            reverse('search_content'),
            {
                'q': 'photography',
                'category': self.category1.id,
                'tag': self.tag1.id
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertEqual(response.context['posts'][0], self.post1)

    def test_search_pagination(self):
        """Test search results pagination"""
        # Create more posts
        for i in range(15):
            Post.objects.create(
                creator=self.creator,
                title=f'Post {i}',
                text=f'Content {i}',
                visibility='public'
            )
        
        response = self.client.get(
            reverse('search_content'),
            {'page': 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_next'])
        self.assertTrue(response.context['has_previous'])

    def test_search_empty_results(self):
        """Test search with no results"""
        response = self.client.get(
            reverse('search_content'),
            {'q': 'nonexistent'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)
        self.assertContains(response, 'No results found') 