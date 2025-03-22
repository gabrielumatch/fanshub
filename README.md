# FansHub

FansHub is a content creator platform that allows creators to share content with their subscribers and manage different levels of content visibility.

## Features

### Content Visibility System

Posts on FansHub can have three visibility levels:

1. **Public** 
   - Visible to everyone, including non-registered users
   - Great for promotional content and attracting new subscribers
   - No payment required

2. **Subscribers Only**
   - Only visible to users with an active subscription to the creator
   - Core content that subscribers get access to with their monthly subscription
   - Protected by the subscription paywall

3. **Premium**
   - Special content that requires an additional one-time payment
   - Available for purchase even by existing subscribers
   - Ideal for exclusive or special content beyond regular subscription benefits

### Subscription System

- Monthly subscription model
- Creators set their own subscription price
- Subscribers get access to all "Subscribers Only" content
- Subscription auto-renews unless cancelled
- Subscribers can manage their subscriptions and payment methods

### Creator Features

- Customizable profile with cover photo and avatar
- Content management dashboard
- Post creation with multiple media support (images and videos)
- Revenue tracking and analytics
- Subscriber management tools

### User Features

- Easy subscription management
- Content feed from subscribed creators
- Profile customization
- Secure payment processing through Stripe

## Technical Details

### Post Model
```python
class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public - Visible to everyone'),
        ('subscribers', 'Subscribers Only - Visible to subscribers'),
        ('premium', 'Premium - Requires additional payment'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Media Model
```python
class Media(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    file = models.FileField(upload_to='post_media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
```

### Subscription Model
```python
class Subscription(models.Model):
    subscriber = models.ForeignKey(User, related_name='subscriptions')
    creator = models.ForeignKey(User, related_name='subscribers')
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

## Payment Processing

- Integrated with Stripe for secure payment processing
- Handles both subscription payments and one-time purchases
- Automatic subscription renewal
- Secure payment method storage

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/fanshub.git
cd fanshub
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations
```bash
python manage.py migrate
```

6. Start the development server
```bash
python manage.py runserver
```

## Environment Variables

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `STRIPE_PUBLIC_KEY`: Your Stripe public key
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built inspired by OnlyFans and other content subscription platforms
- Uses Bootstrap 5 for UI components
- Powered by Django, Supabase, and Stripe
