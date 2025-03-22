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

## Test Coverage

### Unit Tests

#### Authentication & User Management
- [x] User registration
- [x] User login/logout
- [x] Profile management
- [x] Password reset
- [x] Email verification
- [x] Two-factor authentication

#### Content Management
- [x] Post creation
- [x] Post editing
- [x] Post deletion
- [x] Media upload
- [x] Content visibility
- [x] Content moderation
- [x] Content categories
- [x] Content tags

#### Social Features
- [x] Liking posts
- [x] Commenting on posts
- [x] Following creators
- [x] Sharing content
- [x] Saving posts
- [x] Content reporting

#### Subscription System
- [x] Subscription creation
- [x] Subscription cancellation
- [x] Subscription renewal
- [x] Subscription tiers
- [x] Subscription status

#### Payment System
- [x] Payment method management
- [x] Payment processing
- [x] Invoice generation
- [x] Refund handling
- [x] Payment history

### Integration Tests

#### Creator Dashboard
- [x] Dashboard overview
- [x] Content management
- [x] Analytics
- [x] Earnings tracking
- [x] Subscriber management

#### Search & Discovery
- [x] Content search
- [x] Creator search
- [x] Category browsing
- [x] Tag filtering
- [x] Trending content
- [x] Recommended creators

#### Notifications
- [x] Notification creation
- [x] Notification delivery
- [x] Notification preferences
- [x] Notification management
- [x] Real-time updates

#### Privacy & Security
- [x] Content blocking
- [x] User blocking
- [x] Content reporting
- [x] Data privacy
- [x] Security measures

### End-to-End Tests

#### User Journeys
- [x] Registration flow
- [x] Login flow
- [x] Profile setup
- [x] Content creation
- [x] Subscription process
- [x] Payment flow

#### Content Interactions
- [x] Post viewing
- [x] Media handling
- [x] Comment system
- [x] Like system
- [x] Share functionality
- [x] Save functionality

#### Dashboard Functionality
- [x] Analytics viewing
- [x] Content management
- [x] Subscription management
- [x] Payment management
- [x] Settings configuration

### API Tests

#### Authentication
- [x] Token generation
- [x] Token validation
- [x] Permission checks
- [x] Rate limiting

#### Content Endpoints
- [x] Post CRUD
- [x] Media handling
- [x] Category management
- [x] Tag management

#### User Endpoints
- [x] Profile management
- [x] Settings management
- [x] Preferences management

#### Payment Endpoints
- [x] Payment processing
- [x] Subscription management
- [x] Invoice generation

#### Notification Endpoints
- [x] Notification creation
- [x] Notification retrieval
- [x] Notification management

## Running Tests

### Prerequisites
- Python 3.8+
- Virtual environment
- Chrome WebDriver (for Selenium tests)

### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test content.tests.test_social_features

# Run tests with coverage
coverage run manage.py test
coverage report
coverage html
```

### Test Files Structure
```
tests/
├── content/
│   ├── test_social_features.py
│   ├── test_templates.py
│   ├── test_javascript.py
│   └── test_search.py
├── accounts/
│   ├── test_auth.py
│   └── test_privacy.py
├── payments/
│   ├── test_payment.py
│   └── test_subscription.py
├── notifications/
│   └── test_notifications.py
├── api/
│   └── test_api.py
└── e2e/
    └── test_user_journeys.py
```

## Test Coverage Requirements

- Minimum coverage: 80%
- Critical paths: 100%
- API endpoints: 100%
- Authentication flows: 100%
- Payment processing: 100%

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Merges to main branch
- Scheduled daily runs

## Test Maintenance

- Update tests when adding new features
- Review test coverage regularly
- Maintain test data fixtures
- Keep test dependencies updated

## Contributing

When adding new features or modifying existing ones, please ensure:

1. Write unit tests for new functionality
2. Update existing tests if modifying features
3. Add integration tests for external service interactions
4. Include end-to-end tests for critical user flows
5. Maintain test coverage above 80%

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built inspired by OnlyFans and other content subscription platforms
- Uses Bootstrap 5 for UI components
- Powered by Django, Supabase, and Stripe
