from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.urls import reverse

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
            media_files = []
            for media_form in formset:
                if media_form.cleaned_data.get('file'):
                    media = media_form.save(commit=False)
                    media.post = post
                    media.save()
                    media_files.append({
                        'id': media.id,
                        'url': media.file.url,
                        'type': media.media_type
                    })
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('post_detail', args=[post.id]),
                    'post': {
                        'id': post.id,
                        'title': post.title,
                        'text': post.text,
                        'visibility': post.visibility,
                        'price': str(post.price) if post.price else None,
                        'media': media_files
                    }
                })
            
            messages.success(request, _('Your post has been created successfully.'))
            return redirect('post_detail', post_id=post.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'form': form.errors,
                        'media': formset.errors
                    }
                })
    else:
        form = PostForm()
        formset = MediaFormSet(prefix='media')
    
    return render(request, 'content/create_post.html', {
        'form': form,
        'formset': formset
    })

@login_required
def post_detail(request, post_id):
    """View a post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can view this post
    can_view = True
    
    # Check visibility permissions
    if post.visibility in ['subscribers', 'premium']:
        if request.user == post.creator:
            can_view = True
        else:
            # Check if user is subscribed
            is_subscribed = Subscription.objects.filter(
                subscriber=request.user,
                creator=post.creator,
                active=True
            ).exists()
            
            # For premium content, user must be subscribed and pay the additional fee
            if post.visibility == 'premium':
                # TODO: Implement premium content purchase check
                can_view = False
            else:
                can_view = is_subscribed
    
    context = {
        'post': post,
        'can_view': can_view,
        'is_subscriber': Subscription.objects.filter(
            subscriber=request.user,
            creator=post.creator,
            active=True
        ).exists() if request.user.is_authenticated else False
    }
    
    return render(request, 'content/post_detail.html', context)

@login_required
def edit_post(request, post_id):
    """Edit an existing post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is the creator
    if request.user != post.creator:
        messages.error(request, _('You can only edit your own posts.'))
        return redirect('post_detail', post_id=post.id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        formset = MediaFormSet(request.POST, request.FILES, instance=post, prefix='media')
        
        if form.is_valid() and formset.is_valid():
            post = form.save()
            formset.save()
            
            messages.success(request, _('Your post has been updated successfully.'))
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
        formset = MediaFormSet(instance=post, prefix='media')
    
    return render(request, 'content/edit_post.html', {
        'form': form,
        'formset': formset,
        'post': post
    })

@login_required
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            post.comments.create(
                user=request.user,
                content=content
            )
            messages.success(request, _('Your comment has been added successfully.'))
        else:
            messages.error(request, _('Comment content cannot be empty.'))
    
    return redirect('post_detail', post_id=post.id)
