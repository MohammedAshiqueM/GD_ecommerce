# Generated by Django 5.0.6 on 2024-07-13 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Admin_side', '0039_alter_productoffer_unique_together_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productoffer',
            old_name='proproduct_configurationduct',
            new_name='proproduct_configurationd',
        ),
    ]