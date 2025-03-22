from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Subscription(models.Model):
    """
    Subscription model to track user subscriptions to creators
    """
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='subscribers'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.creator.username}"
    
    class Meta:
        unique_together = ('subscriber', 'creator')
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

class PaymentHistory(models.Model):
    """
    Payment History model to track all payments
    """
    PAYMENT_TYPES = (
        ('subscription', _('Subscription Payment')),
        ('tip', _('Tip')),
        ('post', _('Post Purchase')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('succeeded', _('Succeeded')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments_made'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments_received'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Optional relations to related objects
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payments'
    )
    post = models.ForeignKey(
        'content.Post', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payments'
    )
    
    def __str__(self):
        return f"{self.payment_type} payment of ${self.amount} from {self.user.username} to {self.recipient.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Payment History')
        verbose_name_plural = _('Payment History')

class SavedPaymentMethod(models.Model):
    """
    Model to store user's saved payment methods
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255)
    last4 = models.CharField(max_length=4)
    brand = models.CharField(max_length=50)  # visa, mastercard, etc.
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Saved Payment Method')
        verbose_name_plural = _('Saved Payment Methods')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.brand} card ending in {self.last4}"

    def save(self, *args, **kwargs):
        # If this is set as default, unset any other default payment methods
        if self.is_default:
            SavedPaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
