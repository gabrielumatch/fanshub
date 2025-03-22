from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Post(models.Model):
    """
    Post model for creator content
    """
    VISIBILITY_CHOICES = [
        ('public', _('Public - Visible to everyone')),
        ('subscribers', _('Subscribers Only - Visible to subscribers')),
        ('premium', _('Premium - Requires additional payment')),
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
