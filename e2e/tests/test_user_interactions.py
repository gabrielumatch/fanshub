from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from django.contrib.auth import get_user_model
from content.models import Post
from django.core.files.uploadedfile import SimpleUploadedFile
import time

User = get_user_model()

class UserInteractionTests(LiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        
        # Create test users
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
        
        # Create test post
        self.post = Post.objects.create(
            creator=self.creator,
            title='Test Post',
            text='Test content',
            visibility='public'
        )

    def tearDown(self):
        self.driver.quit()

    def test_complete_user_journey(self):
        """Test complete user journey from registration to subscription"""
        # Registration
        self.driver.get(f'{self.live_server_url}/register/')
        self.driver.find_element(By.NAME, 'username').send_keys('newuser')
        self.driver.find_element(By.NAME, 'email').send_keys('newuser@example.com')
        self.driver.find_element(By.NAME, 'password1').send_keys('testpass123')
        self.driver.find_element(By.NAME, 'password2').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify registration success
        self.assertIn('Profile', self.driver.title)
        
        # Login
        self.driver.find_element(By.LINK_TEXT, 'Logout').click()
        self.driver.find_element(By.LINK_TEXT, 'Login').click()
        self.driver.find_element(By.NAME, 'username').send_keys('newuser')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Browse creator profile
        self.driver.get(f'{self.live_server_url}/creator/{self.creator.username}/')
        self.assertIn(self.creator.username, self.driver.title)
        
        # Subscribe to creator
        self.driver.find_element(By.CSS_SELECTOR, 'a[href*="subscribe"]').click()
        # Note: Payment processing would be mocked in a real test
        
        # View premium content
        self.driver.get(f'{self.live_server_url}/post/{self.post.id}/')
        self.assertIn(self.post.title, self.driver.title)

    def test_content_interactions(self):
        """Test content interactions (like, comment, share)"""
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # View post
        self.driver.get(f'{self.live_server_url}/post/{self.post.id}/')
        
        # Like post
        like_button = self.driver.find_element(By.CSS_SELECTOR, '[data-action="like"]')
        like_button.click()
        time.sleep(1)  # Wait for AJAX request
        
        # Add comment
        comment_form = self.driver.find_element(By.CSS_SELECTOR, 'form[action*="add_comment"]')
        comment_form.find_element(By.TAG_NAME, 'textarea').send_keys('Test comment')
        comment_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(1)  # Wait for page reload
        
        # Verify comment
        self.assertIn('Test comment', self.driver.page_source)

    def test_creator_dashboard(self):
        """Test creator dashboard functionality"""
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('creator')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Access dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        self.assertIn('Dashboard', self.driver.title)
        
        # Create new post
        self.driver.find_element(By.LINK_TEXT, 'Create Post').click()
        self.driver.find_element(By.NAME, 'title').send_keys('New Test Post')
        self.driver.find_element(By.NAME, 'text').send_keys('New test content')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify post creation
        self.assertIn('New Test Post', self.driver.page_source)

    def test_subscription_management(self):
        """Test subscription management"""
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Access subscription management
        self.driver.get(f'{self.live_server_url}/subscriptions/manage/')
        self.assertIn('Manage Subscriptions', self.driver.title)
        
        # Test subscription cancellation
        cancel_button = self.driver.find_element(By.CSS_SELECTOR, '[data-action="cancel"]')
        cancel_button.click()
        
        # Fill cancellation form
        modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'cancelSubscriptionModal'))
        )
        modal.find_element(By.ID, 'cancellation_reason').send_keys('too_expensive')
        modal.find_element(By.CSS_SELECTOR, 'button.btn-danger').click()
        
        # Verify cancellation
        time.sleep(1)  # Wait for AJAX request
        self.assertIn('Cancelled', self.driver.page_source)

    def test_profile_management(self):
        """Test profile management"""
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('subscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Access profile settings
        self.driver.get(f'{self.live_server_url}/profile/edit/')
        self.assertIn('Edit Profile', self.driver.title)
        
        # Update profile
        self.driver.find_element(By.NAME, 'bio').send_keys('Updated bio')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify update
        self.assertIn('Updated bio', self.driver.page_source)

    def test_search_and_discovery(self):
        """Test search and discovery features"""
        self.driver.get(f'{self.live_server_url}/discover/')
        
        # Test search
        search_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="search"]')
        search_input.send_keys('creator')
        search_input.send_keys(Keys.RETURN)
        time.sleep(1)  # Wait for search results
        
        # Verify search results
        self.assertIn('creator', self.driver.page_source.lower())
        
        # Test category filtering
        self.driver.find_element(By.CSS_SELECTOR, 'a[href*="category"]').click()
        time.sleep(1)  # Wait for filter results
        
        # Test sorting
        self.driver.find_element(By.CSS_SELECTOR, 'select[name="sort"]').click()
        self.driver.find_element(By.CSS_SELECTOR, 'option[value="popular"]').click()
        time.sleep(1)  # Wait for sort results 