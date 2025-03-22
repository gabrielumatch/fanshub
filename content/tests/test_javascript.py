from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post, Media
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

User = get_user_model()

class JavaScriptTests(TestCase):
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
        
        # Set up Selenium WebDriver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.driver.quit()

    def test_like_post_interaction(self):
        """Test like post functionality"""
        self.driver.get(f'{self.live_server_url}/post/{self.post.id}/')
        self.driver.find_element(By.CSS_SELECTOR, '[data-action="like"]').click()
        time.sleep(1)  # Wait for AJAX request
        
        # Verify like count updated
        like_count = self.driver.find_element(By.ID, 'like-count')
        self.assertEqual(like_count.text, '1')
        
        # Verify heart icon color changed
        heart_icon = self.driver.find_element(By.CSS_SELECTOR, '.bi-heart')
        self.assertIn('text-danger', heart_icon.get_attribute('class'))

    def test_comment_submission(self):
        """Test comment submission functionality"""
        self.driver.get(f'{self.live_server_url}/post/{self.post.id}/')
        
        # Login
        self.driver.find_element(By.LINK_TEXT, 'Login').click()
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Submit comment
        comment_form = self.driver.find_element(By.CSS_SELECTOR, 'form[action*="add_comment"]')
        comment_form.find_element(By.TAG_NAME, 'textarea').send_keys('Test comment')
        comment_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(1)  # Wait for page reload
        
        # Verify comment appears
        self.assertIn('Test comment', self.driver.page_source)

    def test_subscription_modal(self):
        """Test subscription modal functionality"""
        self.driver.get(f'{self.live_server_url}/creator/{self.creator.username}/')
        
        # Click subscribe button
        self.driver.find_element(By.CSS_SELECTOR, 'a[href*="subscribe"]').click()
        time.sleep(1)  # Wait for modal
        
        # Verify modal content
        modal = self.driver.find_element(By.ID, 'subscriptionModal')
        self.assertTrue(modal.is_displayed())
        self.assertIn('Subscribe', modal.text)
        
        # Close modal
        self.driver.find_element(By.CSS_SELECTOR, '.btn-close').click()
        time.sleep(1)
        self.assertFalse(modal.is_displayed())

    def test_image_preview(self):
        """Test image preview functionality"""
        # Create test image
        media_file = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        media = Media.objects.create(
            post=self.post,
            file=media_file,
            media_type='image'
        )
        
        self.driver.get(f'{self.live_server_url}/post/{self.post.id}/')
        
        # Click image
        image = self.driver.find_element(By.CSS_SELECTOR, '.post-media')
        image.click()
        time.sleep(1)
        
        # Verify lightbox
        lightbox = self.driver.find_element(By.CSS_SELECTOR, '.lightbox')
        self.assertTrue(lightbox.is_displayed())
        
        # Close lightbox
        self.driver.find_element(By.CSS_SELECTOR, '.lightbox-close').click()
        time.sleep(1)
        self.assertFalse(lightbox.is_displayed())

    def test_infinite_scroll(self):
        """Test infinite scroll functionality"""
        # Create multiple posts
        for i in range(15):
            Post.objects.create(
                creator=self.creator,
                title=f'Test Post {i}',
                text=f'Test content {i}',
                visibility='public'
            )
        
        self.driver.get(f'{self.live_server_url}/creator/{self.creator.username}/')
        
        # Scroll to bottom
        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)
        
        # Verify more posts loaded
        posts = self.driver.find_elements(By.CSS_SELECTOR, '.post-card')
        self.assertGreater(len(posts), 10)

    def test_search_autocomplete(self):
        """Test search autocomplete functionality"""
        self.driver.get(f'{self.live_server_url}/discover/')
        
        # Type in search box
        search_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="search"]')
        search_input.send_keys('test')
        time.sleep(1)
        
        # Verify suggestions appear
        suggestions = self.driver.find_element(By.CSS_SELECTOR, '.search-suggestions')
        self.assertTrue(suggestions.is_displayed())
        
        # Click suggestion
        suggestion = self.driver.find_element(By.CSS_SELECTOR, '.suggestion-item')
        suggestion.click()
        time.sleep(1)
        
        # Verify search results
        self.assertIn('test', self.driver.page_source.lower())

    def test_notification_badge(self):
        """Test notification badge functionality"""
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Create notification
        self.post.likes.create(user=self.creator)
        
        # Verify notification badge
        badge = self.driver.find_element(By.CSS_SELECTOR, '.notification-badge')
        self.assertEqual(badge.text, '1')
        
        # Click notification
        badge.click()
        time.sleep(1)
        
        # Verify notification list
        notifications = self.driver.find_element(By.CSS_SELECTOR, '.notification-list')
        self.assertTrue(notifications.is_displayed())

    def test_stripe_payment_form(self):
        """Test Stripe payment form integration"""
        self.driver.get(f'{self.live_server_url}/creator/{self.creator.username}/')
        
        # Login
        self.driver.find_element(By.LINK_TEXT, 'Login').click()
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Click subscribe
        self.driver.find_element(By.CSS_SELECTOR, 'a[href*="subscribe"]').click()
        time.sleep(1)
        
        # Verify Stripe elements
        self.assertIn('stripe', self.driver.page_source.lower())
        self.assertIn('card-element', self.driver.page_source.lower())

    def test_responsive_navigation(self):
        """Test responsive navigation menu"""
        self.driver.set_window_size(375, 812)  # iPhone X size
        
        self.driver.get(f'{self.live_server_url}/')
        
        # Click menu button
        menu_button = self.driver.find_element(By.CSS_SELECTOR, '.navbar-toggler')
        menu_button.click()
        time.sleep(1)
        
        # Verify menu items
        menu_items = self.driver.find_elements(By.CSS_SELECTOR, '.navbar-nav .nav-item')
        self.assertTrue(len(menu_items) > 0)
        
        # Click menu item
        menu_items[0].click()
        time.sleep(1)
        
        # Verify menu closed
        self.assertFalse(menu_items[0].is_displayed()) 