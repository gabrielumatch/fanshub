from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register the User model with the admin site
admin.site.register(User, UserAdmin)

# Add fields to the admin display
UserAdmin.fieldsets += (
    ('Profile', {'fields': ('bio', 'profile_picture', 'cover_photo', 'date_of_birth')}),
    ('Creator Settings', {'fields': ('is_creator', 'subscription_price', 'stripe_account_id')}),
)
