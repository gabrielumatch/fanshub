from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from .models import Post, Media
from .forms import PostForm, MediaFormSet
from accounts.models import User
from subscriptions.models import Subscription

def home(request):
    """Home page view"""
    # Check if user is authenticated
    if request.user.is_authenticated:
        # Get subscribed creators
        subscriptions = Subscription.objects.filter(
            subscriber=request.user, 
            active=True
        ).values_list('creator_id', flat=True)
        
        # Get posts from subscribed creators
        posts = Post.objects.filter(creator_id__in=subscriptions).order_by('-created_at')
        
        # If user has no subscriptions, show featured creators
        if not posts:
            featured_creators = User.objects.filter(is_creator=True).order_by('?')[:5]
            context = {
                'featured_creators': featured_creators,
                'no_subscriptions': True
            }
            return render(request, 'content/home.html', context)
        
        return render(request, 'content/home.html', {'posts': posts})
    else:
        # For non-authenticated users, show landing page with featured creators
        featured_creators = User.objects.filter(is_creator=True).order_by('?')[:5]
        return render(request, 'content/landing.html', {'featured_creators': featured_creators})

def discover(request):
    """Discover creators"""
    creators = User.objects.filter(is_creator=True).order_by('?')
    return render(request, 'content/discover.html', {'creators': creators})

@login_required
def create_post(request):
    """Create a new post"""
    if not request.user.is_creator:
        messages.error(request, _('You need to be a creator to create posts.'))
        return redirect('become_creator')
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        formset = MediaFormSet(request.POST, request.FILES, prefix='media')
        
        if form.is_valid() and formset.is_valid():
            post = form.save(commit=False)
            post.creator = request.user
            post.save()
            
            # Save media files
            for media_form in formset:
                if media_form.cleaned_data.get('file'):
                    media = media_form.save(commit=False)
                    media.post = post
                    media.save()
            
            messages.success(request, _('Your post has been created successfully.'))
            return redirect('profile')
    else:
        form = PostForm()
        formset = MediaFormSet(prefix='media')
    
    return render(request, 'content/create_post.html', {'form': form, 'formset': formset})

@login_required
def post_detail(request, post_id):
    """View a post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can view this post
    can_view = True
    
    # If it's a paid post, check if user is subscribed or is the creator
    if post.is_paid:
        if request.user == post.creator:
            can_view = True
        else:
            is_subscribed = Subscription.objects.filter(
                subscriber=request.user,
                creator=post.creator,
                active=True
            ).exists()
            can_view = is_subscribed
    
    context = {
        'post': post,
        'can_view': can_view
    }
    return render(request, 'content/post_detail.html', context)
