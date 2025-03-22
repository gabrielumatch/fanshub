# FansHub - OnlyFans Clone

A content subscription platform built with Django, Supabase, and Stripe. FansHub allows creators to share exclusive content with subscribers, who pay monthly subscription fees to access it.

## Project Overview

This project implements a platform similar to OnlyFans where:

- **Creators** can share content (images, videos, text) and set subscription prices
- **Users** can subscribe to creators to access their exclusive content
- **Payments** are processed securely through Stripe
- **Data** is stored in Supabase (PostgreSQL)

## Features Implemented

- **User Authentication System**

  - Custom User model with profile fields
  - Registration and login functionality
  - Profile management with cover photos and profile pictures

- **Creator Features**

  - Creator profiles with customizable subscription pricing
  - Stripe integration for creator accounts
  - Dashboard for creators to track subscribers and stats

- **Content Management**

  - Post model for creators to share content
  - Media model for images and videos
  - Premium vs free content options

- **Subscription System**

  - Subscription model with Stripe integration
  - Payment processing and tracking
  - Access control for premium content

- **User Experience**
  - Responsive design using Bootstrap 5
  - Discover page for finding creators
  - Feed of subscribed content

## Technologies Used

- **Backend**: Django 5.1, Django REST Framework
- **Database**: SQLite (local), Supabase (production)
- **Authentication**: Django built-in auth + Supabase
- **Payment Processing**: Stripe API
- **Frontend**: HTML, CSS, Bootstrap 5
- **Storage**: Media files stored locally (configurable for cloud storage)

## Project Structure

- **accounts** - User authentication and profile management
- **content** - Posts and media content management
- **subscriptions** - Payment processing and subscription handling

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- virtualenv

### Installation

1. Clone the repository:

```
git clone https://github.com/yourusername/fanshub.git
cd fanshub
```

2. Create and activate a virtual environment:

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Configure environment variables:
   Create a `.env` file in the project root with the following variables:

```
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key

STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

MEDIA_URL=/media/
MEDIA_ROOT=media/
```

5. Run migrations:

```
python manage.py migrate
```

6. Create a superuser:

```
python manage.py createsuperuser
```

7. Run the development server:

```
python manage.py runserver
```

8. Visit `http://localhost:8000` in your browser.

## Implementation Details

- Custom user model extending Django's AbstractUser
- Stripe integration for subscription payments
- Media handling for creator content
- Webhook handling for Stripe events
- Bootstrap 5 for responsive UI

## Future Improvements

- Direct messaging between creators and subscribers
- Tipping functionality
- Content scheduling
- Analytics dashboard for creators
- Email notifications
- Social sharing features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built inspired by OnlyFans and other content subscription platforms
- Uses Bootstrap 5 for UI components
- Powered by Django, Supabase, and Stripe
