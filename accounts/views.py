from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import stripe
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, CreatorProfileForm
from .models import User
from subscriptions.models import Subscription, PaymentHistory
from content.models import Post

stripe.api_key = settings.STRIPE_SECRET_KEY

def register(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Registration successful. Welcome to FansHub!'))
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """Handle user login"""
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('You have been logged in successfully.'))
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    user_posts = Post.objects.filter(creator=user).order_by('-created_at')
    subscriptions = Subscription.objects.filter(subscriber=user)
    
    # Debug print statements
    print(f"User: {user.username}")
    print(f"Is creator: {user.is_creator}")
    print(f"Number of posts: {user_posts.count()}")
    for post in user_posts:
        print(f"Post ID: {post.id}")
        print(f"Post Title: {post.title}")
        print(f"Post Text: {post.text[:20]}...")
        print(f"Post Visibility: {post.visibility}")
        print(f"Post Created At: {post.created_at}")
        print("---")
    print(f"Number of subscriptions: {subscriptions.count()}")
    
    context = {
        'user': user,
        'user_posts': user_posts,
        'subscriptions': subscriptions,
    }
    
    print("\nContext being passed to template:")
    print(f"user: {context['user'].username}")
    print(f"user_posts count: {len(context['user_posts'])}")
    print(f"subscriptions count: {len(context['subscriptions'])}")
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated successfully.'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def become_creator(request):
    """Handle becoming a creator"""
    if request.user.is_creator:
        messages.info(request, _('You are already a creator.'))
        return redirect('creator_dashboard')
    
    if request.method == 'POST':
        form = CreatorProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                # Create a customer for the creator
                customer = stripe.Customer.create(
                    email=request.user.email,
                    metadata={
                        'user_id': request.user.id,
                        'username': request.user.username
                    }
                )
                
                user = form.save(commit=False)
                user.is_creator = True
                user.stripe_customer_id = customer.id
                user.save()
                
                messages.success(request, _('Congratulations! You are now a creator.'))
                return redirect('creator_dashboard')
            except stripe.error.StripeError as e:
                messages.error(request, f"Stripe error: {str(e)}")
    else:
        form = CreatorProfileForm(instance=request.user)
    
    return render(request, 'accounts/become_creator.html', {'form': form})

@login_required
def creator_dashboard(request):
    """Display creator dashboard"""
    if not request.user.is_creator:
        messages.error(request, _('You need to be a creator to access the dashboard.'))
        return redirect('become_creator')
    
    # Get creator stats
    posts_count = Post.objects.filter(creator=request.user).count()
    subscribers_count = Subscription.objects.filter(creator=request.user, active=True).count()
    
    # Calculate monthly revenue
    monthly_revenue = PaymentHistory.objects.filter(
        recipient=request.user,
        payment_type='subscription',
        status='succeeded',
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate engagement rate (placeholder for now)
    engagement_rate = 0
    
    # Get recent posts
    recent_posts = Post.objects.filter(creator=request.user).order_by('-created_at')[:5]
    
    # Get recent subscribers
    recent_subscribers = User.objects.filter(
        subscriptions__creator=request.user,
        subscriptions__active=True
    ).distinct().order_by('-date_joined')[:5]
    
    context = {
        'posts_count': posts_count,
        'subscribers_count': subscribers_count,
        'monthly_revenue': monthly_revenue,
        'engagement_rate': engagement_rate,
        'recent_posts': recent_posts,
        'recent_subscribers': recent_subscribers,
    }
    return render(request, 'accounts/creator_dashboard.html', context)

def creator_profile(request, username):
    """View a creator's public profile"""
    creator = get_object_or_404(User, username=username, is_creator=True)
    is_subscribed = False
    subscription = None
    
    # Check if the user is subscribed to this creator
    if request.user.is_authenticated:
        subscription = Subscription.objects.filter(
            subscriber=request.user, 
            creator=creator, 
            active=True
        ).first()
        is_subscribed = subscription is not None
    
    # Get creator's posts
    if is_subscribed or request.user == creator:
        # Show all posts for subscribers or the creator themselves
        posts = Post.objects.filter(creator=creator).order_by('-created_at')
    else:
        # Show only public posts for non-subscribers
        posts = Post.objects.filter(creator=creator, visibility='public').order_by('-created_at')
    
    # Get creator stats
    posts_count = Post.objects.filter(creator=creator).count()
    subscribers_count = Subscription.objects.filter(creator=creator, active=True).count()
    
    context = {
        'creator': creator,
        'posts': posts,
        'is_subscribed': is_subscribed,
        'subscription': subscription,
        'posts_count': posts_count,
        'subscribers_count': subscribers_count,
    }
    return render(request, 'accounts/creator_profile.html', context)

@login_required
def settings_view(request):
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.bio = request.POST.get('bio')

        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        # Handle cover photo
        if 'cover_photo' in request.FILES:
            user.cover_photo = request.FILES['cover_photo']

        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')

        try:
            user.save()
            messages.success(request, 'Settings updated successfully.')
            return redirect('settings')
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')

    return render(request, 'accounts/settings.html')
