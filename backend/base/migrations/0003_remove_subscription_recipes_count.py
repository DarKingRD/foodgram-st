# Generated by Django 4.2.18 on 2025-01-27 22:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_subscription_recipes_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='recipes_count',
        ),
    ]
