from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import stripe

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, CreatorProfileForm
from .models import User
from subscriptions.models import Subscription
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
    """Display user profile"""
    user_posts = Post.objects.filter(creator=request.user).order_by('-created_at')
    subscriptions = Subscription.objects.filter(subscriber=request.user, active=True)
    
    context = {
        'user': request.user,
        'user_posts': user_posts,
        'subscriptions': subscriptions,
    }
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
            # Create a Stripe account for the creator
            try:
                account = stripe.Account.create(
                    type="express",
                    country="US",
                    email=request.user.email,
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                )
                
                user = form.save(commit=False)
                user.is_creator = True
                user.stripe_account_id = account.id
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
    
    # TODO: Fetch earnings data from Stripe
    
    context = {
        'posts_count': posts_count,
        'subscribers_count': subscribers_count,
    }
    return render(request, 'accounts/creator_dashboard.html', context)

def creator_profile(request, username):
    """View a creator's public profile"""
    creator = get_object_or_404(User, username=username, is_creator=True)
    is_subscribed = False
    
    # Check if the user is subscribed to this creator
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user, 
            creator=creator, 
            active=True
        ).exists()
    
    # Get creator's posts
    if is_subscribed or request.user == creator:
        # Show all posts for subscribers or the creator themselves
        posts = Post.objects.filter(creator=creator).order_by('-created_at')
    else:
        # Show only free posts for non-subscribers
        posts = Post.objects.filter(creator=creator, is_paid=False).order_by('-created_at')
    
    context = {
        'creator': creator,
        'posts': posts,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'accounts/creator_profile.html', context)
