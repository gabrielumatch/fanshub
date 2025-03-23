from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

class UserLoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    cover_photo = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ('bio', 'profile_picture', 'cover_photo', 'date_of_birth')

class CreatorProfileForm(forms.ModelForm):
    """Form for creator-specific profile settings"""
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True,
        help_text=_('Tell your potential subscribers about yourself')
    )
    subscription_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        help_text=_('Monthly subscription price for your content')
    )
    verification_document = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text=_('Please upload a valid ID document (passport, RG, ID) for verification. This is required for creator accounts.')
    )
    
    class Meta:
        model = User
        fields = ('bio', 'subscription_price', 'verification_document')
        
    def clean_subscription_price(self):
        price = self.cleaned_data['subscription_price']
        if price < 0:
            raise forms.ValidationError(_('Price cannot be negative'))
        return price
        
    def clean_verification_document(self):
        document = self.cleaned_data.get('verification_document')
        if document:
            # Check file size (max 5MB)
            if document.size > 5 * 1024 * 1024:
                raise forms.ValidationError(_('File size must be no more than 5MB'))
            
            # Check file type (allow common document formats)
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if document.content_type not in allowed_types:
                raise forms.ValidationError(_('Only PDF, JPEG, and PNG files are allowed'))
        return document 