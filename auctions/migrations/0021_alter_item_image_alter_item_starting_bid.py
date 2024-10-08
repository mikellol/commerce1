# Generated by Django 5.1 on 2024-09-06 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0020_alter_item_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='image',
            field=models.ImageField(blank=True, default='default-image.jpg', upload_to='imagenes_raza/'),
        ),
        migrations.AlterField(
            model_name='item',
            name='starting_bid',
            field=models.IntegerField(),
        ),
    ]
