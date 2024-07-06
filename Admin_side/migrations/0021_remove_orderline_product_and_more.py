# Generated by Django 5.0.6 on 2024-07-04 03:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0020_alter_order_shipping_method'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderline',
            name='product',
        ),
        migrations.AddField(
            model_name='orderline',
            name='product_configuration',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Admin_side.productconfiguration'),
        ),
    ]