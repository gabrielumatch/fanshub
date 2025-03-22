from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    """
    Category model for content categorization
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']

class Tag(models.Model):
    """
    Tag model for content tagging
    """
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']

class Post(models.Model):
    """
    Post model for creator content
    """
    VISIBILITY_CHOICES = [
        ('public', _('Public - Visible to everyone')),
        ('subscribers', _('Subscribers Only - Visible to subscribers')),
        ('premium', _('Premium - Requires additional payment')),
        ('private', _('Private - Only visible to creator')),
    ]
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200, default='Untitled Post')
    text = models.TextField()
    visibility = models.CharField(
        max_length=20, 
        choices=VISIBILITY_CHOICES,
        default='public',
        help_text=_('Choose who can see this post')
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_('Price for premium content (only if visibility is set to Premium)')
    )
    categories = models.ManyToManyField(Category, related_name='posts', blank=True)
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.creator.username}'s post: {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

class Media(models.Model):
    """
    Media model for images and videos attached to posts
    """
    MEDIA_TYPES = [
        ('image', _('Image')),
        ('video', _('Video')),
    ]
    
    file = models.FileField(upload_to='post_media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='media_files')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.media_type} for {self.post.title}"
    
    class Meta:
        verbose_name = _('Media')
        verbose_name_plural = _('Media')

class Comment(models.Model):
    """
    Comment model for post comments
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_comments', blank=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

class Like(models.Model):
    """
    Like model for post likes
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')

class Share(models.Model):
    """
    Share model for post shares
    """
    SHARE_PLATFORMS = [
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('linkedin', _('LinkedIn')),
        ('whatsapp', _('WhatsApp')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shares')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=SHARE_PLATFORMS)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Share of {self.post.title} on {self.platform} by {self.user.username}"
    
    class Meta:
        verbose_name = _('Share')
        verbose_name_plural = _('Shares')

class Save(models.Model):
    """
    Save model for saved posts
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = _('Save')
        verbose_name_plural = _('Saves')
