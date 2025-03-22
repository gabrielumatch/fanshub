from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class LandingPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.landing_url = reverse('landing')
        
        # Create some featured creators
        for i in range(3):
            creator = User.objects.create_user(
                username=f'creator{i}',
                email=f'creator{i}@example.com',
                password='testpass123',
                is_creator=True
            )
            creator.profile.subscription_price = 10.00
            creator.profile.bio = f'Test bio for creator {i}'
            creator.profile.save()

    def test_landing_page_loads(self):
        """Test that landing page loads correctly"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'content/landing.html')

    def test_landing_page_featured_creators(self):
        """Test featured creators display"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['featured_creators']), 3)
        
        for creator in response.context['featured_creators']:
            self.assertTrue(creator.is_creator)
            self.assertEqual(creator.profile.subscription_price, 10.00)

    def test_landing_page_creator_cards(self):
        """Test creator cards display"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        # Check creator card elements
        for i in range(3):
            self.assertContains(response, f'creator{i}')
            self.assertContains(response, '$10.00/month')
            self.assertContains(response, 'Test bio for creator')

    def test_landing_page_creator_photos(self):
        """Test creator profile pictures display"""
        # Add profile pictures to creators
        for creator in User.objects.filter(is_creator=True):
            profile_pic = SimpleUploadedFile(
                name=f'{creator.username}_pic.jpg',
                content=b'',
                content_type='image/jpeg'
            )
            creator.profile.profile_picture = profile_pic
            creator.profile.save()
        
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        for creator in User.objects.filter(is_creator=True):
            self.assertContains(response, creator.profile.profile_picture.url)

    def test_landing_page_cover_photos(self):
        """Test creator cover photos display"""
        # Add cover photos to creators
        for creator in User.objects.filter(is_creator=True):
            cover_photo = SimpleUploadedFile(
                name=f'{creator.username}_cover.jpg',
                content=b'',
                content_type='image/jpeg'
            )
            creator.profile.cover_photo = cover_photo
            creator.profile.save()
        
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        for creator in User.objects.filter(is_creator=True):
            self.assertContains(response, creator.profile.cover_photo.url)

    def test_landing_page_links(self):
        """Test landing page links"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        # Check registration link
        self.assertContains(response, reverse('register'))
        
        # Check discover link
        self.assertContains(response, reverse('discover'))
        
        # Check creator profile links
        for creator in User.objects.filter(is_creator=True):
            self.assertContains(response, reverse('creator_profile', kwargs={'username': creator.username}))

    def test_landing_page_why_join_section(self):
        """Test 'Why join FansHub?' section"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        # Check section title
        self.assertContains(response, 'Why join FansHub?')
        
        # Check feature cards
        self.assertContains(response, 'Support Creators')
        self.assertContains(response, 'Exclusive Content')
        self.assertContains(response, 'Direct Connection')

    def test_landing_page_hero_section(self):
        """Test hero section content"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        
        # Check hero text
        self.assertContains(response, 'Connect with your favorite creators')
        self.assertContains(response, 'Subscribe to creators, access exclusive content')
        
        # Check hero buttons
        self.assertContains(response, 'Join Now')
        self.assertContains(response, 'Discover Creators') 