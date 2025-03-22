from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from content.models import Post, Category, Tag
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SearchTests(TestCase):
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
        
        # Create test categories
        self.category1 = Category.objects.create(name='Photography')
        self.category2 = Category.objects.create(name='Art')
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='nature')
        self.tag2 = Tag.objects.create(name='portrait')
        
        # Create test posts
        self.post1 = Post.objects.create(
            creator=self.creator,
            title='Beautiful Nature Photo',
            text='A stunning landscape photo',
            visibility='public'
        )
        self.post1.categories.add(self.category1)
        self.post1.tags.add(self.tag1)
        
        self.post2 = Post.objects.create(
            creator=self.creator,
            title='Portrait Art',
            text='Digital portrait artwork',
            visibility='public'
        )
        self.post2.categories.add(self.category2)
        self.post2.tags.add(self.tag2)

    def test_search_by_title(self):
        """Test searching posts by title"""
        response = self.client.get(reverse('search'), {'q': 'Nature'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertNotContains(response, 'Portrait Art')

    def test_search_by_content(self):
        """Test searching posts by content"""
        response = self.client.get(reverse('search'), {'q': 'landscape'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertNotContains(response, 'Portrait Art')

    def test_search_by_category(self):
        """Test searching posts by category"""
        response = self.client.get(reverse('search'), {'category': 'Photography'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertNotContains(response, 'Portrait Art')

    def test_search_by_tag(self):
        """Test searching posts by tag"""
        response = self.client.get(reverse('search'), {'tag': 'nature'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertNotContains(response, 'Portrait Art')

    def test_search_by_creator(self):
        """Test searching posts by creator"""
        response = self.client.get(reverse('search'), {'creator': 'creator'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertContains(response, 'Portrait Art')

    def test_search_with_multiple_filters(self):
        """Test searching with multiple filters"""
        response = self.client.get(reverse('search'), {
            'q': 'Nature',
            'category': 'Photography',
            'tag': 'nature'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')
        self.assertNotContains(response, 'Portrait Art')

    def test_search_empty_results(self):
        """Test search with no results"""
        response = self.client.get(reverse('search'), {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No results found')

    def test_search_pagination(self):
        """Test search results pagination"""
        # Create multiple posts
        for i in range(15):
            Post.objects.create(
                creator=self.creator,
                title=f'Test Post {i}',
                text=f'Test content {i}',
                visibility='public'
            )
        
        # Test first page
        response = self.client.get(reverse('search'), {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post 0')
        
        # Test second page
        response = self.client.get(reverse('search'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post 10')

    def test_search_sorting(self):
        """Test search results sorting"""
        # Create posts with different dates
        old_post = Post.objects.create(
            creator=self.creator,
            title='Old Post',
            text='Old content',
            visibility='public',
            created_at=timezone.now() - timedelta(days=7)
        )
        
        new_post = Post.objects.create(
            creator=self.creator,
            title='New Post',
            text='New content',
            visibility='public',
            created_at=timezone.now()
        )
        
        # Test sorting by date
        response = self.client.get(reverse('search'), {'sort': 'date'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('New Post', response.content.decode())
        self.assertIn('Old Post', response.content.decode())

    def test_search_visibility(self):
        """Test search with different content visibility"""
        # Create private post
        private_post = Post.objects.create(
            creator=self.creator,
            title='Private Post',
            text='Private content',
            visibility='private'
        )
        
        # Test search as non-authenticated user
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private Post')
        
        # Test search as authenticated user
        self.client.login(username='subscriber', password='testpass123')
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private Post')

    def test_search_autocomplete(self):
        """Test search autocomplete functionality"""
        response = self.client.get(reverse('search_autocomplete'), {'q': 'Nat'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful Nature Photo')

    def test_search_filters_persistence(self):
        """Test that search filters persist in the URL"""
        response = self.client.get(reverse('search'), {
            'q': 'Nature',
            'category': 'Photography',
            'tag': 'nature'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Nature"')
        self.assertContains(response, 'value="Photography"')
        self.assertContains(response, 'value="nature"')

    def test_search_invalid_page(self):
        """Test search with invalid page number"""
        response = self.client.get(reverse('search'), {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page 1')

    def test_search_special_characters(self):
        """Test search with special characters"""
        special_post = Post.objects.create(
            creator=self.creator,
            title='Special @#$% Post',
            text='Content with special characters',
            visibility='public'
        )
        
        response = self.client.get(reverse('search'), {'q': '@#$%'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Special @#$% Post')

    def test_search_creators(self):
        """Test searching for creators"""
        response = self.client.get(
            reverse('content:search'),
            {'q': 'creator', 'type': 'creators'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('creator', response.json()['results'][0]['username'])

    def test_search_content(self):
        """Test searching for content"""
        response = self.client.get(
            reverse('content:search'),
            {'q': 'portrait', 'type': 'content'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['title'], 'Portrait Photography')

    def test_filter_by_category(self):
        """Test filtering content by category"""
        response = self.client.get(
            reverse('content:search'),
            {'category': self.category1.id}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['category'], 'Photography')

    def test_filter_by_tag(self):
        """Test filtering content by tag"""
        response = self.client.get(
            reverse('content:search'),
            {'tag': self.tag1.id}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertIn('nature', [tag['name'] for tag in response.json()['results'][0]['tags']])

    def test_sort_by_popularity(self):
        """Test sorting content by popularity"""
        # Add likes to posts
        self.post2.likes.create(user=self.subscriber)
        
        response = self.client.get(
            reverse('content:search'),
            {'sort': 'popular'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['title'], 'Portrait Art')

    def test_sort_by_date(self):
        """Test sorting content by date"""
        # Create newer post
        newer_post = Post.objects.create(
            creator=self.creator,
            title='New Post',
            text='Latest content',
            visibility='public'
        )
        
        response = self.client.get(
            reverse('content:search'),
            {'sort': 'newest'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['title'], 'New Post')

    def test_trending_creators(self):
        """Test trending creators section"""
        # Add subscribers to creator
        self.creator.subscribers.add(self.subscriber)
        
        response = self.client.get(reverse('content:trending_creators'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['creators']), 1)
        self.assertEqual(response.json()['creators'][0]['username'], 'creator')

    def test_recommended_creators(self):
        """Test recommended creators for logged-in user"""
        self.client.login(username='subscriber', password='testpass123')
        
        response = self.client.get(reverse('content:recommended_creators'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['creators']), 1)
        self.assertEqual(response.json()['creators'][0]['username'], 'creator')

    def test_category_browsing(self):
        """Test browsing content by category"""
        response = self.client.get(
            reverse('content:category', args=[self.category1.slug])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['posts']), 1)
        self.assertEqual(response.json()['posts'][0]['category'], 'Photography')

    def test_tag_browsing(self):
        """Test browsing content by tag"""
        response = self.client.get(
            reverse('content:tag', args=[self.tag1.slug])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['posts']), 1)
        self.assertIn('nature', [tag['name'] for tag in response.json()['posts'][0]['tags']])

    def test_search_with_multiple_criteria(self):
        """Test searching with multiple criteria"""
        response = self.client.get(
            reverse('content:search'),
            {
                'q': 'portrait',
                'category': self.category1.id,
                'tag': self.tag1.id
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['title'], 'Portrait Photography')

    def test_search_pagination(self):
        """Test pagination of search results"""
        # Create multiple posts
        for i in range(15):
            Post.objects.create(
                creator=self.creator,
                title=f'Test Post {i}',
                text=f'Test content {i}',
                visibility='public'
            )
        
        response = self.client.get(
            reverse('content:search'),
            {'page': 1}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 10)  # Default page size

    def test_search_empty_results(self):
        """Test search with no results"""
        response = self.client.get(
            reverse('content:search'),
            {'q': 'nonexistent'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

    def test_search_suggestions(self):
        """Test search suggestions"""
        response = self.client.get(
            reverse('content:search_suggestions'),
            {'q': 'port'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('portrait', [suggestion['text'] for suggestion in response.json()['suggestions']])

    def test_related_content(self):
        """Test related content suggestions"""
        response = self.client.get(
            reverse('content:related_content', args=[self.post1.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['related_posts']), 1)
        self.assertEqual(response.json()['related_posts'][0]['title'], 'Portrait Art') 