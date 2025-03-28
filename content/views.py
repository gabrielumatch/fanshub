from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, F, Max, Count
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.utils import timezone
import os

from .models import Post, Media, Like, Chat, Message
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
        
        # Get posts from subscribed creators with prefetched media
        posts = Post.objects.filter(creator_id__in=subscriptions).prefetch_related('media_files').order_by('-created_at')
        
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
def delete_post(request, post_id):
    """Delete a post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is the creator
    if request.user != post.creator:
        messages.error(request, _('You can only delete your own posts.'))
        return redirect('post_detail', post_id=post.id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, _('Your post has been deleted successfully.'))
        return redirect('home')
    
    return render(request, 'content/delete_post.html', {'post': post})

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

def creator_profile(request, username):
    creator = get_object_or_404(User, username=username)
    posts = Post.objects.filter(creator=creator, visibility='public').order_by('-created_at')
    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(subscriber=request.user, creator=creator, status='active').exists()
    
    context = {
        'creator': creator,
        'posts': posts,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'accounts/creator_profile.html', context)

@login_required
def like_post(request, post_id):
    """Like or unlike a post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can view this post
    if post.visibility in ['subscribers', 'premium']:
        if request.user != post.creator:
            is_subscribed = Subscription.objects.filter(
                subscriber=request.user,
                creator=post.creator,
                active=True
            ).exists()
            if not is_subscribed:
                return JsonResponse({
                    'success': False,
                    'message': _('You need to be subscribed to like this post.')
                }, status=403)
    
    # Toggle like
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
    
    return JsonResponse({
        'success': True,
        'is_liked': is_liked,
        'likes_count': post.likes.count()
    })

@login_required
def chat_list(request):
    """List all chats for the current user"""
    # Get all chats where user is either creator or subscriber
    chats = Chat.objects.filter(
        Q(creator=request.user) | Q(subscriber=request.user)
    ).select_related('creator', 'subscriber').annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by(Coalesce('last_message_time', F('created_at')).desc())
    
    context = {
        'chats': chats,
        'is_creator': request.user.is_creator
    }
    return render(request, 'content/chat_list.html', context)

@login_required
def chat_detail(request, chat_id):
    """View a specific chat"""
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Check if user is part of this chat
    if request.user not in [chat.creator, chat.subscriber]:
        messages.error(request, _('You do not have permission to view this chat.'))
        return redirect('chat_list')
    
    # Get the other user
    other_user = chat.subscriber if request.user == chat.creator else chat.creator
    
    # Mark unread messages as read
    Message.objects.filter(
        chat=chat,
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    # Get messages with sender info
    messages_list = Message.objects.filter(chat=chat).select_related('sender').order_by('created_at')
    
    context = {
        'chat': chat,
        'messages': messages_list,
        'other_user': other_user,
        'debug': True  # Enable debug mode for development
    }
    return render(request, 'content/chat_detail.html', context)

@login_required
def start_chat(request, username):
    """Start a new chat with a creator"""
    creator = get_object_or_404(User, username=username, is_creator=True)
    
    # Check if chat already exists
    existing_chat = Chat.objects.filter(
        (Q(creator=creator) & Q(subscriber=request.user)) |
        (Q(creator=request.user) & Q(subscriber=creator))
    ).first()
    
    if existing_chat:
        return redirect('chat_detail', chat_id=existing_chat.id)
    
    # Create new chat
    if request.user.is_creator:
        # If both users are creators, the initiator becomes the creator in the chat
        chat = Chat.objects.create(creator=request.user, subscriber=creator)
    else:
        chat = Chat.objects.create(creator=creator, subscriber=request.user)
    
    return redirect('chat_detail', chat_id=chat.id)

@require_POST
def upload_chat_media(request, chat_id):
    try:
        file = request.FILES.get('media')
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        # Create a unique filename
        file_extension = os.path.splitext(file.name)[1]
        filename = f'chat_{chat_id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_extension}'
        
        # Save the file
        path = default_storage.save(f'chat_media/{filename}', file)
        url = default_storage.url(path)
        
        # Determine media type
        media_type = 'image' if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif'] else 'video'
        
        return JsonResponse({
            'url': url,
            'media_type': media_type
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
