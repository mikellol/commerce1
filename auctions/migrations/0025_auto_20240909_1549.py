# Generated by Django 3.2 on 2024-09-09 21:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0024_auctionhistory_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auctionhistory',
            name='date_won',
        ),
        migrations.RemoveField(
            model_name='auctionhistory',
            name='status',
        ),
    ]
