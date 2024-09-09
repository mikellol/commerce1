from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
import logging
from django.db import models
from django.shortcuts import render, get_object_or_404, reverse 
from .models import Item, Bid
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Item, ItemCategory
import logging
import os  
from .models import User, Bid, Item, ItemComment, Watchlist, ItemCategory, AuctionHistory
from .utils import utility
import json 
from django.core import serializers
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)
#Define forms based on models


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'image', 'starting_bid']
        labels = {
            'title': 'Lote',
            'description': 'Nombre',
            'image': 'Imagen',
            'starting_bid': 'Precio'
        }
        widgets = {
        'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lote'}),
        'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
        'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'item_img_url'}),
        'starting_bid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Precio inicial'})
        }

class Comment(models.Model):
    comment = models.TextField(max_length=256)

class CommentForm(forms.Form):
    class Meta:
        model = Comment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                 'class':"form-control",
                 'id':"textAreaComment",
                 'rows':"2", 'placeholder':"Type a comment"
            })
        }

def index(request):
    # Obtener todos los items y usuarios
    items = utility.get_items() or []
    distinct_users = utility.get_users_with_items() or []
    
    # Serializar datos a JSON
    json_data = serializers.serialize("json", items)
    json_users = json.dumps(distinct_users)
    
    message = ""
    
    if request.method == 'POST':        
        listing_title = str(request.POST.get("listing_title", False))
        try:
            item_ = Item.objects.get(title=listing_title)
            user_ = User.objects.get(username=request.user.username)
            
            # Buscar item en watchlist
            search_item = Watchlist.objects.filter(items=item_, user=user_)
            if not search_item.exists():
                message = "Item added to watchlist"
                Watchlist.objects.create(items=item_, user=user_)
            else:
                message = "Item has already been added to watchlist"
        except Item.DoesNotExist:
            message = "Item not found"
        except User.DoesNotExist:
            message = "User not found"
    
    # Preparar bids y items
    items_with_bids = Item.objects.filter(user_bid_items__items__isnull=False).distinct()
    bids = []

    for item in items:
        if item in items_with_bids:
            bid = Bid.objects.filter(items=item).order_by('amount').last()
            bids.append(bid.amount if bid else item.starting_bid)
        else:
            bids.append(item.starting_bid)
    
    logger.info(f"Bids: {bids}")
    items_bids = list(zip(items, bids))
    
    # Preparar el contexto para la plantilla
    context = {
        "items": items,
        "items_bids": items_bids,
        "json": json_data,
        "json_users": json_users,
        "commentForm": CommentForm(),
        "message": message,
        'is_index': True
    }
    
    return render(request, "auctions/index.html", context)
    
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))

def register(request):
    if request.method == "POST":
        commentForm = CommentForm(request.POST)
        # if commentForm.is_valid():
            #logger.infor(commentForm)

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })
        username=request.POST["username"]
        email=request.POST["email"]
        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

def add(request):
    if request.method == 'POST':
        add_item_form = ItemForm(request.POST, request.FILES)
        if add_item_form.is_valid():
            item_title = add_item_form.cleaned_data['title']
            item_desc = add_item_form.cleaned_data['description']
            item_image = request.FILES.get('image')
            item_str_bid = add_item_form.cleaned_data['starting_bid']
            
            # Create a new Item
            new_item = Item(
                user=request.user,
                title=item_title,
                description=item_desc,
                starting_bid=item_str_bid
            )
            
            # Save the Item instance
            new_item.save()
            logger.debug("Item saved with ID: %s", new_item.id)
            
            # Save the uploaded image
            if item_image:
                # Construct the image path
                image_dir = f'imagenes_raza/{new_item.id}/'
                image_path = os.path.join(image_dir, item_image.name)
                logger.debug("Saving image to path: %s", image_path)
                
                # Save the image to the filesystem
                try:
                    # Ensure the directory exists
                    if not os.path.exists(default_storage.path(image_dir)):
                        os.makedirs(default_storage.path(image_dir))
                    
                    # Save the file to the constructed path
                    with default_storage.open(image_path, 'wb+') as destination:
                        for chunk in item_image.chunks():
                            destination.write(chunk)
                    logger.debug("Image saved successfully to %s", image_path)
                except Exception as e:
                    logger.error("Error saving image: %s", e)
                
                # Update the Item instance with the image path
                new_item.image = image_path
                new_item.save()
                logger.debug("Item updated with image path")
            else:
                logger.warning("No image found in the request")
            
            return redirect('auctions:index')
        else:
            logger.error("Form is invalid: %s", add_item_form.errors)
            return render(request, "auctions/add.html", {
                "new_form": add_item_form,
                "message": "Invalid Data"
            })
    else:
        logger.debug("Received GET request")
        return render(request, "auctions/add.html", {
            "new_form": ItemForm()
        })
    
@login_required
def cards_view(request):
    # Get the current user
    user = get_object_or_404(User, username=request.user.username)
    
    # Get items associated with the user, handling cases where there might be no items
    items = Item.objects.filter(user=user)
    if not items:
        # Handle the case where the user has no items
        return render(request, "auctions/cards.html", {
            "user": user,
            "item": None,
            "description": "No items available."
        })
    
    # Get the first item or handle index error
    item = items[0]  # You can change the logic to select a different item if needed
    description = str(item.description)[:40] + ".."
    
    # Optionally, get the bid information if applicable
    last_bid = Bid.objects.filter(item=item).order_by('-timestamp').first()  # Fetch the latest bid

    # Render the template with the item and user information
    return render(request, "auctions/cards.html", {
        "user": user,
        "item": item,
        "description": description,
        "last_bid": last_bid  # Pass last_bid if you want to display bid information
    })

def listing_details_view(request, id=None):
    # Fetch the item by ID or title
    if id:
        item_ = get_object_or_404(Item, id=id)
    else:
        listing_title = request.POST.get("listing_title") or request.GET.get("listing_title")
        item_ = get_object_or_404(Item, title=listing_title)

    # Get the owner of the item
    owner = item_.user
    
    # Get all comments related to the item
    comments = item_.comments_list.all()
    
    # Check if there are any bids for this item
    search_bid = Bid.objects.filter(items=item_)
    
    # Determine if the current user owns this item
    own_this_item = (item_.user.username == request.user.username)
    
    # Handle the message_bid if it's available in the GET request
    message_bid = request.GET.get("message_bid", "Couldn't place the bid.")
    
    # Determine the last bid for the item
    last_bid = search_bid.order_by('amount').last() if search_bid.exists() else None

    # Get the three most recent bids
    recent_bids = Bid.objects.filter(items=item_).order_by('-created_at')[:3]

    # Render the template with the appropriate context
    return render(request, "auctions/listing_details.html", {
        "item": item_,
        "owner": owner,
        "comments": comments,
        "last_bid": last_bid,
        "privilege": own_this_item,
        "message_bid": message_bid,
        "recent_bids": recent_bids,  # Pass the recent bids to the template
    })

@login_required
def add_comment(request):
    if request.method == 'POST':
        #Get important things: username, commented item title, and user making the comment
        item_name = request.POST.get('listing_title')
        comment = str(request.POST.get('commentText'))
        item_obj = Item.objects.filter(title=item_name).get()
        author = User.objects.filter(username = request.user.username).get()
        new_comment = ItemComment(text=comment, author=author, item=item_obj)
        new_comment.save()    
    return HttpResponseRedirect(reverse("auctions:listing_details")+"?listing_title="+item_name+"")

def watchlist_view(request):
    #Get all watchlist objects related to the current user
    current_user = User.objects.filter(username=request.user.username).get()
    watchlist = current_user.watchlist_list.all()    
    return render(request, "auctions/watchlist.html",{
        "watchlist": watchlist
    })
    # items = utility.get_items()
    # distinct_users = utility.get_users_with_items()
    # json_data = serializers.serialize("json", items)
    # json_users = json.dumps(distinct_users)
    # if items != None:
    #     return render(request, "auctions/index.html",{
    #         "items":items,
    #         "json":json_data,
    #         "json_users": json_users
    #     })
    # else:
    #     return render(request, "auctions/index.html")

def delete_item_watchlist(request):
    current_user = User.objects.filter(username=request.user.username).get()
    if request.method == 'POST':
        item_name = request.POST.get('listing_title')
        item_ = Item.objects.filter(title=item_name).get()
        watchlist_item = current_user.watchlist_list.filter(items=item_).get()
        watchlist_item.delete()
    watchlist = current_user.watchlist_list.all()
    return render(request, "auctions/watchlist.html",{
        "watchlist": watchlist
    })

def category_list_redirect(request, category):
    _category = str(category)
    # _items = ItemCategory.objects.filter(name=_category)
    _items = Item.objects.filter(category=_category)
    items_with_bids =  Item.objects.filter(user_bid_items__items__isnull=False).distinct()
    #Match both list
    items_with_bids_as_set = set(items_with_bids)
    intersection = items_with_bids_as_set.intersection(_items)
    intersection_list = list(intersection)
    bids_for_items = []
    logger.info(_items)
    for item in _items:
        if item.category == _category and item.status==True:
            if item in intersection_list:
                bids_for_items.append(Bid.objects.filter(items=item).order_by('amount').last().amount)
            else:
                bids_for_items.append(item.starting_bid)
    items_bids = list(zip(_items,bids_for_items))

    return render(request, "auctions/category_listing.html", {
        "category":_category,
        "items": _items,
        "items_bids": items_bids
    })

def category_list(request):
    category_choices = [
            ('clothing', 'Clothing'),
            ('toys', 'Toys'),
            ('electronics', 'Electronics'),
            ('art','Art')]
    return render(request, "auctions/categories.html",{
        "categories":category_choices
    })

def add_to_watchlist(request):
      if request.method == 'POST':        
        listing_title = str(request.POST.get("listing_title", False))
        item_ = Item.objects.filter(title=listing_title).get()
        user_ = User.objects.filter(username=request.user.username).get()
        #Search for item in watchlist
        search_item = Watchlist.objects.filter(items=item_, user=user_)
        if len(search_item)!=0:
            message="Item added to watchlist"
            # Watchlist(items=item_, user=user_).save()
        else:
            message="Item Has already been added to watchlist"
        return HttpResponseRedirect(reverse("auctions:index", kwargs={"message":'Hello'}))

@login_required
def place_bid(request):
    if request.method == 'POST':
        bid = float(request.POST.get("new_bid", 0))
        item_id = int(request.POST.get("item_id", 0))
        item_ = get_object_or_404(Item, id=item_id)
        user_ = get_object_or_404(User, username=request.user.username)
        
        search_bid = Bid.objects.filter(items=item_)
        if not search_bid.exists():
            starting_bid = float(item_.starting_bid)
            if bid > starting_bid:
                new_bid = Bid(user=user_, amount=bid, items=item_)
                new_bid.save()
                message = "Bid placed successfully"
            else:
                message = "The bid must be greater than the starting bid"
        else:
            placed_bids = Bid.objects.filter(items=item_).order_by('amount')
            last_bid = placed_bids.last()
            if bid > last_bid.amount:
                new_bid = Bid(user=user_, amount=bid, items=item_)
                new_bid.save()
                message = "Bid placed successfully"
            else:
                message = "The bid must be greater than the current bid"

        return HttpResponseRedirect(reverse('auctions:listing_details', args=[item_.id]) + f"?message_bid={message}")
    else:
        return HttpResponseRedirect(reverse('auctions:index'))
    
@login_required
def end_listing(request):
    if request.method == 'POST':
        item_id = request.POST.get("item_id")
        
        if not item_id:
            return HttpResponseNotFound("Item ID is required")

        try:
            item_ = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return HttpResponseNotFound("Item not found")

        placed_bids = Bid.objects.filter(items=item_).order_by('amount')
        last_bid = placed_bids.last()

        if last_bid:
            best_bid_user = last_bid.user
            auction_history = AuctionHistory(user=best_bid_user, items=item_)
            auction_history.save()
            logger.info(f"Auction history saved for item '{item_.title}' with winner '{best_bid_user.username}' and bid amount '{last_bid.amount}'")
        else:
            logger.info(f"No bids found for item '{item_.title}'. Auction ended without a winner.")
            # Opcionalmente puedes registrar el historial de subastas para los casos sin oferta

        # Actualiza el estado del ítem para indicar que la subasta ha terminado
        item_.status = False
        item_.save()

    return HttpResponseRedirect(reverse('auctions:index'))

def auctions_history(request):
    user = request.user
    
    # Filtra el historial de subastas para el usuario autenticado
    auction_history = AuctionHistory.objects.filter(user=user)
    
    items = []
    bids = []
    
    if auction_history.exists():
        message = ""
        for auction_item in auction_history:
            # Filtrar correctamente por 'items', que es la clave foránea en Bid
            bid_item = Bid.objects.filter(items=auction_item.items, user=user).order_by('-created_at').first()
            
            # Si hay una oferta, añádela a la lista de ofertas
            if bid_item:
                bids.append(bid_item)
                items.append(auction_item.items)
        
        # Empareja artículos con sus ofertas correspondientes
        items_bids = list(zip(items, bids))
        
        # Ordena por la fecha de creación de las ofertas, de más reciente a más antigua
        items_bids.sort(key=lambda x: x[1].created_at, reverse=True)
        
        return render(request, "auctions/auctions_won.html", {
            "items_bids": items_bids,
            "message": message
        })
    else:
        message = "You have not won any auction yet."
        return render(request, "auctions/auctions_won.html", {
            "message": message
        })
