from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User


class User(AbstractUser):
    def __str__(self):
        return f"{self.first_name}"

class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="item_list")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=256, blank=True)
    image = models.ImageField(upload_to='imagenes_raza/', blank=True, default='default-image.jpg')
    starting_bid = models.IntegerField()
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set the field to now when the object is first created


    def __str__(self):
        return f"{self.title}, {self.description}"

class ItemCategory(models.Model):
    name = models.CharField(max_length=24, blank=False)
    item = models.ForeignKey(Item, blank=True, on_delete=models.CASCADE, related_name="category_list")

    def __str__(self):
        return f"{self.name}"

class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_bids")
    amount = models.DecimalField(decimal_places=2, max_digits=8)
    items = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="user_bid_items", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set the field to now when the object is first created

    def __str__(self):
        return f"{self.amount}"
    
class ItemComment(models.Model):
    text = models.TextField(max_length=512, blank=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="comments_list")
    author = models.ForeignKey(User, on_delete=models.CASCADE)

class Watchlist(models.Model):
    items = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_list')

    def __str__(self):
        return f"{self.items}, {self.user}"

class Category(models.Model):
    name = models.CharField(max_length=24, blank=False)
    items = models.ManyToManyField(Item, blank=True, related_name="categories")

    def __str__(self):
        return f"{self.name}"

class AuctionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="history_user")
    items = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="items_auction_history")

    def __str__(self):
        return f"{self.user.first_name}, {self.items}"


