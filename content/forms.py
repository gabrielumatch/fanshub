from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Post, Media

class PostForm(forms.ModelForm):
    """Form for creating and editing posts"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
        required=True
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your post content here...'}),
        required=True
    )
    visibility = forms.ChoiceField(
        choices=Post.VISIBILITY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='public',
        help_text=_('Choose who can see this post')
    )
    price = forms.DecimalField(
        required=False,
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0.00', 
            'min': '0', 
            'step': '0.01',
            'disabled': 'disabled'  # Will be enabled via JavaScript when premium is selected
        }),
        help_text=_('Price for premium content')
    )
    
    class Meta:
        model = Post
        fields = ['title', 'text', 'visibility', 'price']

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get('visibility')
        price = cleaned_data.get('price')
        
        if visibility == 'premium' and (price is None or price <= 0):
            raise forms.ValidationError(_('You must set a price greater than zero for premium content.'))
        elif visibility != 'premium' and price:
            cleaned_data['price'] = None  # Clear price if post is not premium
        
        return cleaned_data

class MediaForm(forms.ModelForm):
    """Form for adding media to posts"""
    media_type = forms.ChoiceField(
        choices=Media.MEDIA_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    thumbnail = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False,
        help_text=_('Thumbnail for video content (optional)')
    )
    
    class Meta:
        model = Media
        fields = ('media_type', 'file', 'thumbnail')

# Create a formset for adding multiple media files to a post
MediaFormSet = inlineformset_factory(
    Post, Media,
    form=MediaForm,
    extra=3,  # Number of empty forms to display
    can_delete=True
) 