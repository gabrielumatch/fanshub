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

### Unit Tests

#### Authentication & User Management
- [x] User registration
- [x] User login/logout
- [x] Password reset
- [x] Profile editing
- [x] Two-factor authentication
- [x] Session management
- [x] User blocking
- [x] Privacy settings

#### Content Management
- [x] Post creation
- [x] Post editing
- [x] Post deletion
- [x] Media upload
- [x] Content visibility rules
- [x] Content moderation
- [x] Content reporting
- [x] Content blocking

#### Social Features
- [x] Liking posts
- [x] Commenting on posts
- [x] Following creators
- [x] Sharing posts
- [x] User interactions
- [x] Content engagement

#### Subscription System
- [x] Subscription creation
- [x] Subscription cancellation
- [x] Subscription renewal
- [x] Subscription status
- [x] Subscription history
- [x] Subscription plans

#### Payment System
- [x] Payment method management
- [x] Payment processing
- [x] Subscription billing
- [x] Payment history
- [x] Invoice generation
- [x] Payment webhooks
- [x] Payment failure handling

#### Creator Dashboard
- [x] Dashboard overview
- [x] Content management
- [x] Subscriber management
- [x] Analytics
- [x] Revenue tracking
- [x] Content scheduling

#### Search & Discovery
- [x] Content search
- [x] Creator search
- [x] Category filtering
- [x] Tag filtering
- [x] Trending content
- [x] Recommended creators
- [x] Search suggestions

#### Notifications
- [x] New subscriber notifications
- [x] New comment notifications
- [x] New like notifications
- [x] Subscription notifications
- [x] Payment notifications
- [x] Content approval notifications
- [x] Notification preferences
- [x] Notification management

#### Privacy & Security
- [x] Content blocking
- [x] User blocking
- [x] Content reporting
- [x] Content moderation
- [x] Privacy settings
- [x] Two-factor authentication
- [x] Session management
- [x] IP blocking
- [x] Data privacy compliance

#### API Endpoints
- [x] User registration
- [x] User authentication
- [x] Post management
- [x] Subscription management
- [x] Payment method management
- [x] Notification management
- [x] User profile management
- [x] Search functionality
- [x] Rate limiting
- [x] API authentication

### Integration Tests
- [x] Payment method integration with Stripe
- [x] Media processing with AWS S3
- [x] Email service integration
- [x] Push notification service
- [x] Analytics service integration

### End-to-End Tests
- [x] Complete user journey
- [x] Content interactions
- [x] Creator dashboard
- [x] Subscription management
- [x] Profile management
- [x] Search and discovery
- [x] Payment processing
- [x] Notification system

## Running Tests

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r e2e/requirements.txt
```

2. Run all tests:
```bash
python manage.py test
```

3. Run specific test files:
```bash
python manage.py test content.tests.test_ui
python manage.py test e2e.tests.test_user_interactions
```

4. Run tests with coverage:
```bash
coverage run manage.py test
coverage report
coverage html
```

## Test Files Structure

```
├── content/
│   └── tests/
│       ├── test_ui.py
│       ├── test_media.py
│       ├── test_search.py
│       └── test_social_features.py
├── accounts/
│   └── tests/
│       ├── test_auth.py
│       └── test_privacy.py
├── payments/
│   └── tests/
│       └── test_payments.py
├── notifications/
│   └── tests/
│       └── test_notifications.py
├── api/
│   └── tests/
│       └── test_api.py
└── e2e/
    └── tests/
        ├── test_user_flow.py
        └── test_user_interactions.py
```

## Test Coverage

The test suite provides comprehensive coverage of all major features and functionalities:

- Unit tests cover individual components and their interactions
- Integration tests verify external service integrations
- End-to-end tests validate complete user workflows
- UI tests ensure proper rendering and user interactions
- API tests verify REST endpoint functionality

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
