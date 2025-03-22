from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from content.models import Post
from subscriptions.models import Subscription

User = get_user_model()

class UserFlowTests(LiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()  # Make sure ChromeDriver is installed
        self.driver.implicitly_wait(10)
        
        # Create test users
        self.creator = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='testpass123',
            is_creator=True
        )
        self.subscriber = User.objects.create_user(
            username='testsubscriber',
            email='subscriber@test.com',
            password='testpass123'
        )

    def tearDown(self):
        self.driver.quit()

    def test_registration_flow(self):
        """Test complete registration flow"""
        self.driver.get(f'{self.live_server_url}/register/')
        
        # Fill registration form
        self.driver.find_element(By.NAME, 'username').send_keys('newuser')
        self.driver.find_element(By.NAME, 'email').send_keys('new@test.com')
        self.driver.find_element(By.NAME, 'password1').send_keys('newpass123')
        self.driver.find_element(By.NAME, 'password2').send_keys('newpass123')
        self.driver.find_element(By.NAME, 'bio').send_keys('Test bio')
        
        # Submit form
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify redirect to home page
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        
        # Verify user is logged in
        self.assertTrue('newuser' in self.driver.page_source)

    def test_login_flow(self):
        """Test complete login flow"""
        self.driver.get(f'{self.live_server_url}/login/')
        
        # Fill login form
        self.driver.find_element(By.NAME, 'username').send_keys('testsubscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        
        # Submit form
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify redirect to home page
        self.assertEqual(self.driver.current_url, f'{self.live_server_url}/')
        
        # Verify user is logged in
        self.assertTrue('testsubscriber' in self.driver.page_source)

    def test_subscription_flow(self):
        """Test complete subscription flow"""
        # Login as subscriber
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('testsubscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Go to creator profile
        self.driver.get(f'{self.live_server_url}/creator/testcreator/')
        
        # Click subscribe button
        self.driver.find_element(By.CSS_SELECTOR, 'a.btn-primary').click()
        
        # Fill payment form (mocked)
        self.driver.find_element(By.ID, 'card-element').send_keys('4242424242424242')
        self.driver.find_element(By.ID, 'card-expiry').send_keys('12/25')
        self.driver.find_element(By.ID, 'card-cvc').send_keys('123')
        
        # Submit payment
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify subscription success
        self.assertTrue('Successfully subscribed' in self.driver.page_source)

    def test_content_visibility_flow(self):
        """Test content visibility based on subscription status"""
        # Create test posts
        Post.objects.create(
            creator=self.creator,
            title='Public Post',
            text='Public content',
            visibility='public'
        )
        Post.objects.create(
            creator=self.creator,
            title='Premium Post',
            text='Premium content',
            visibility='premium',
            price=10.00
        )
        
        # Test as non-subscriber
        self.driver.get(f'{self.live_server_url}/creator/testcreator/')
        self.assertTrue('Public content' in self.driver.page_source)
        self.assertTrue('Subscribe for' in self.driver.page_source)
        
        # Login as subscriber
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('testsubscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Create subscription
        Subscription.objects.create(
            subscriber=self.subscriber,
            creator=self.creator,
            active=True,
            expires_at='2024-12-31'
        )
        
        # Test as subscriber
        self.driver.get(f'{self.live_server_url}/creator/testcreator/')
        self.assertTrue('Public content' in self.driver.page_source)
        self.assertTrue('Purchase for $10.00' in self.driver.page_source)

    def test_creator_dashboard_flow(self):
        """Test creator dashboard functionality"""
        # Login as creator
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('testcreator')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Go to dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        
        # Create new post
        self.driver.find_element(By.CSS_SELECTOR, 'a.btn-primary').click()
        self.driver.find_element(By.NAME, 'title').send_keys('Test Post')
        self.driver.find_element(By.NAME, 'text').send_keys('Test content')
        self.driver.find_element(By.NAME, 'visibility').send_keys('public')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify post creation
        self.assertTrue('Test Post' in self.driver.page_source)
        self.assertTrue('Test content' in self.driver.page_source)

    def test_payment_method_management_flow(self):
        """Test payment method management"""
        # Login as subscriber
        self.driver.get(f'{self.live_server_url}/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('testsubscriber')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Go to payment methods
        self.driver.get(f'{self.live_server_url}/subscriptions/payment-methods/')
        
        # Add new payment method
        self.driver.find_element(By.CSS_SELECTOR, 'button.btn-primary').click()
        self.driver.find_element(By.ID, 'card-element').send_keys('4242424242424242')
        self.driver.find_element(By.ID, 'card-expiry').send_keys('12/25')
        self.driver.find_element(By.ID, 'card-cvc').send_keys('123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify payment method addition
        self.assertTrue('4242' in self.driver.page_source) 