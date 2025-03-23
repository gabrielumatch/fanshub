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

- **Real-time Chat**
  - Direct messaging between creators and subscribers
  - Real-time message updates
  - Message history
  - Unread message indicators

## Technical Specifications

- **Backend**: Django 4.2
- **Frontend**: Bootstrap 5, JavaScript
- **Database**: PostgreSQL
- **File Storage**: AWS S3
- **Payment Processing**: Stripe
- **Authentication**: Django Auth System
- **Real-time Communication**: Django Channels with Redis
- **Containerization**: Docker

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fanshub.git
cd fanshub
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Redis using Docker:
```bash
docker-compose up -d
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Start the development server:
```bash
# Using Daphne for WebSocket support
daphne -b 0.0.0.0 -p 8000 fanshub.asgi:application
```

## Development

### Running Redis

Redis is required for real-time chat functionality. The project includes a Docker Compose configuration to run Redis:

```bash
# Start Redis
docker-compose up -d

# Stop Redis
docker-compose down

# View Redis logs
docker-compose logs redis
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

### Development Server

For development with WebSocket support, use Daphne instead of the default Django development server:

```bash
daphne -b 0.0.0.0 -p 8000 fanshub.asgi:application
```

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

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built inspired by OnlyFans and other content subscription platforms
- Uses Bootstrap 5 for UI components
- Powered by Django, Supabase, and Stripe
