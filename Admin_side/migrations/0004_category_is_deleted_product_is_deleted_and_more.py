# Generated by Django 5.0.6 on 2024-06-10 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0003_alter_order_user_alter_address_user_alter_cart_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
