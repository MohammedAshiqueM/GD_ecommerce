# Generated by Django 5.0.6 on 2024-06-16 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0007_product_subcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='category_image',
            field=models.ImageField(blank=True, null=True, upload_to='category/'),
        ),
    ]
