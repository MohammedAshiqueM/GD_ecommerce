# Generated by Django 5.0.6 on 2024-07-07 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0022_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='coupons/'),
        ),
        migrations.AddField(
            model_name='coupon',
            name='min_purchase_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
