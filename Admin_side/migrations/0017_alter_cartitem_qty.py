# Generated by Django 5.0.6 on 2024-06-25 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0016_rename_category_variation_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='qty',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
