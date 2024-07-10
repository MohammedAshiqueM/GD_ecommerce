# Generated by Django 5.0.6 on 2024-07-07 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0021_remove_orderline_product_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed')], max_length=10)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('active', models.BooleanField(default=True)),
                ('valid_from', models.DateTimeField()),
                ('valid_to', models.DateTimeField()),
                ('usage_limit', models.PositiveIntegerField(blank=True, null=True)),
                ('used_count', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]