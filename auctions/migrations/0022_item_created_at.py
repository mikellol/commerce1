# Generated by Django 5.1 on 2024-09-08 22:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0021_alter_item_image_alter_item_starting_bid'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2023, 9, 8, 0, 0)),
            preserve_default=False,
        ),
    ]
