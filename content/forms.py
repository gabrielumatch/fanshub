from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Post, Media

class PostForm(forms.ModelForm):
    """Form for creating and editing posts"""
    text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'What\'s on your mind?'}),
        required=False
    )
    is_paid = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Mark as paid content?')
    )
    price = forms.DecimalField(
        required=False,
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        help_text=_('Price for this post (if it\'s paid content)')
    )
    
    class Meta:
        model = Post
        fields = ('text', 'is_paid', 'price')
        
    def clean(self):
        cleaned_data = super().clean()
        is_paid = cleaned_data.get('is_paid')
        price = cleaned_data.get('price')
        
        if is_paid and (price is None or price <= 0):
            raise forms.ValidationError(_('You must set a price greater than zero for paid content.'))
        
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