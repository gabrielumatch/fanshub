# Generated by Django 5.1.7 on 2025-03-23 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_stripe_price_id_user_stripe_product_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False, help_text='Indicates if the creator has been verified by admin'),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_document',
            field=models.FileField(blank=True, help_text='Upload a valid ID document (passport, RG, ID) for verification', null=True, upload_to='verification_documents/'),
        ),
    ]
