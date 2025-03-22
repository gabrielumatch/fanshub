# FansHub - A Platform for Content Creators

FansHub is a modern platform that connects content creators with their fans, enabling direct monetization through subscriptions and premium content.

## Features

- **User Authentication**
  - Secure login and registration system
  - Profile management with customizable avatars and bios
  - Email verification and password recovery
  - Social authentication (coming soon)

- **Creator Profiles**
  - Customizable profile pages
  - Cover photos and profile pictures
  - Bio and social media links
  - Subscription pricing management

- **Content Management**
  - Create and edit posts with text, images, and videos
  - Set content visibility (public, subscribers-only, premium)
  - Media upload with automatic optimization
  - Content scheduling and drafts

- **Subscription System**
  - Multiple subscription tiers
  - Secure payment processing with Stripe
  - Automatic billing and renewal
  - Subscription analytics

- **Payment Methods System**
  - Secure card storage with Stripe
  - Multiple payment method support
  - Default payment method selection
  - Automatic payment method updates

## Technical Specifications

- **Backend**: Django 4.2
- **Frontend**: Bootstrap 5, JavaScript
- **Database**: PostgreSQL
- **File Storage**: AWS S3
- **Payment Processing**: Stripe
- **Authentication**: Django Auth System

## Testing Status

### Authentication & User Management ✅
- [x] User Registration
- [x] User Login/Logout
- [x] Profile Creation
- [x] Profile Editing
- [x] Password Reset
- [x] Email Verification
- [x] Two-Factor Authentication
- [x] Session Management
- [x] Account Deletion

### Content Management ✅
- [x] Post Creation
- [x] Post Editing
- [x] Post Deletion
- [x] Media Upload
- [x] Content Visibility Rules
- [x] Content Moderation
- [x] Content Categories
- [x] Content Tags
- [x] Content Search

### Social Features ✅
- [x] Liking Posts
- [x] Commenting on Posts
- [x] Following Creators
- [x] Sharing Posts
- [x] Saving Posts
- [x] Content Reporting
- [x] User Blocking
- [x] Content Blocking

### Subscription System ✅
- [x] Subscription Creation
- [x] Subscription Cancellation
- [x] Subscription Renewal
- [x] Payment Processing
- [x] Subscription Plans
- [x] Payment Method Management
- [x] Subscription History
- [x] Payment Failure Handling

### Payment System ✅
- [x] Payment Method Addition
- [x] Payment Method Update
- [x] Payment Method Deletion
- [x] Payment Processing
- [x] Refund Handling
- [x] Payment History
- [x] Invoice Generation

### Creator Dashboard ✅
- [x] Dashboard View
- [x] Content Creation
- [x] Analytics
- [x] Revenue Tracking
- [x] Subscriber Management
- [x] Content Performance
- [x] Engagement Metrics

### Search & Discovery ✅
- [x] Content Search
- [x] Creator Search
- [x] Category Browsing
- [x] Tag Browsing
- [x] Trending Content
- [x] Recommended Creators
- [x] Search Filters
- [x] Search Pagination

### Notifications ✅
- [x] New Subscriber Notifications
- [x] New Comment Notifications
- [x] New Like Notifications
- [x] Subscription Renewal Notifications
- [x] Payment Failure Notifications
- [x] Content Approval Notifications
- [x] Notification Preferences
- [x] Notification Cleanup

### Privacy & Security ✅
- [x] Content Blocking
- [x] User Blocking
- [x] Content Reporting
- [x] Content Moderation
- [x] Privacy Settings
- [x] Two-Factor Authentication
- [x] Session Management
- [x] IP Blocking
- [x] Data Privacy Compliance

### API Endpoints ✅
- [x] User Registration API
- [x] User Login API
- [x] Post Management API
- [x] Subscription API
- [x] User Profile API
- [x] Content Search API
- [x] Category API
- [x] Tag API
- [x] Creator Stats API
- [x] Notification API

### End-to-End Tests ✅
- [x] Registration Flow
- [x] Login Flow
- [x] Subscription Flow
- [x] Content Visibility Flow
- [x] Creator Dashboard Flow
- [x] Payment Method Management Flow

## Running Tests

To run the tests, make sure you have activated your virtual environment and installed all dependencies:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python manage.py test

# Run specific test file
python manage.py test accounts.tests.test_auth
python manage.py test content.tests.test_social_features
python manage.py test notifications.tests.test_notifications
python manage.py test api.tests.test_api

# Run tests with coverage
python manage.py test --coverage
```

## Getting Started

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built inspired by OnlyFans and other content subscription platforms
- Uses Bootstrap 5 for UI components
- Powered by Django, Supabase, and Stripe
