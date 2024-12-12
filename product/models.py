from django.db import models
from django.contrib.auth import get_user_model
import uuid
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager

import os



def product_medias_path(instance, filename):
    # Get the product's ID
    product_id = instance.product.id

    # Generate the file path: products/product_id/medias/filename
    return os.path.join('products', str(product_id), 'medias', filename)

CONDITIONS_CHOICES = [
        ('new', 'New'),
        ('used_like_new', 'Used(Like New)'),
        ('used_good', 'Used(Good)'),
        ('used', 'Used'),
    ]

AVAILABILITY_CHOISES = [
        ("single_item", "List as Single Item"),
        ("in_stock", "List as In Stock"),
    ]

# class Parent_category(models.Model):
#     name = models.CharField(max_length=100)
    
#     def __str__(self):
#         return self.name
    
class Item_category(models.Model):
    name = models.CharField(max_length=100)
    # parent_category = models.ForeignKey(Parent_category, on_delete=models.PROTECT, related_name = "children_category")

    def __str__(self):
        return self.name
    
class Vehicle_category(models.Model):
    name = models.CharField(max_length=100)
    # parent_category = models.ForeignKey(Parent_category, on_delete=models.PROTECT, related_name = "children_category")

    def __str__(self):
        return self.name
class House_category(models.Model):
    name = models.CharField(max_length=100)
    # parent_category = models.ForeignKey(Parent_category, on_delete=models.PROTECT, related_name = "children_category")

    def __str__(self):
        return self.name
    
class Product_tag(models.Model):
    name = models.CharField(max_length= 100)

    def __str__(self):
        return self.name
    
# class Delivery_method(models.Model):
#     method = models.CharField(max_length= 100)

#     def __str__(self):
#         return self.method
    
class Product(PolymorphicModel):
    class ProductObjects(PolymorphicManager):
        def get_queryset(self):
            return super().get_queryset().filter(status='published')

    
    STATUS_CHOISES = [
        ('published', 'Published'),
        ('draft', 'Draft'),
    ] 
    TYPE_CHOICES = (
        ('item', 'Item'),
        ('house', 'House'),
        ('vehicle', 'Vehicle'),
    )

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # quantity_available = models.PositiveIntegerField(null=True, blank=True)
    tags = models.ManyToManyField(Product_tag, related_name="tags")
    description = models.TextField(null=True, blank=True)

    latitude = models.DecimalField(max_digits=9, null=True, blank=True, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, null=True, blank=True, decimal_places=6) 
       
    product_status = models.CharField(max_length=20, choices=STATUS_CHOISES, default='published')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

 

    objects = PolymorphicManager()
    productobjects = ProductObjects() 

    # def get_type(self):
    #     if isinstance(self, Item):
    #         print("Item Type")
    #         return "ItemType"
    #     elif isinstance(self, Vehicle):
    #         print("Vehicle Type")
    #         return "VehicleType"
    #     elif isinstance(self, House):
    #         print("House Type")
    #         return "HouseType"
    #     print("Unknown Type")
    #     return "Unknown"

    # def __str__(self):
    #     if self.__class__.__name__ == "Product":
    #         return "ItemType"
    #     elif isinstance(self, Vehicle):
    #         return "VehicleType"
    #     elif isinstance(self, House):
    #         return "HouseType"
    #     return "Unknown"
    


class Item(Product):
    DELIVERY_METHODS =[
        ("meet_in_public", "Meet in public")
    ]

    name = models.CharField(max_length=255, null=True, blank=True)
    category = models.ForeignKey(Item_category, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    item_condition = models.CharField(max_length=30, null=True, blank=True, choices=CONDITIONS_CHOICES) 
    delivery_method = models.CharField(max_length=30, null=True, blank=True, choices=DELIVERY_METHODS, default="meet_in_public")
    availability_status = models.CharField(max_length=30, null=True, blank=True, choices=AVAILABILITY_CHOISES, default="single_item")
    def save(self, *args, **kwargs):
        self.type = 'item'
        super().save(*args, **kwargs)
    

class House(Product):
    category = models.ForeignKey(House_category, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    def save(self, *args, **kwargs):
        self.type = 'house'
        super().save(*args, **kwargs)

class Vehicle(Product):
    make = models.CharField(max_length=80, null=True, blank=True)
    category = models.ForeignKey(Vehicle_category, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    vehicle_condition = models.CharField(max_length=30, null=True, blank=True, choices=CONDITIONS_CHOICES) 

    model = models.CharField(max_length=80, null=True, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True) 
    year = models.CharField(null=True, blank=True, max_length=5)
    def save(self, *args, **kwargs):
        self.type = 'vehicle'
        super().save(*args, **kwargs)
    
# class Post(models.Model):
#     product = models.OneToOneField(Product, null=True, blank=True, related_name='post')

class Media(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='medias')
    media = models.FileField(default=None, null=True, blank=True, upload_to=product_medias_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)

    def __str__(self):
        return self.product.owner.first_name

# class City(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name

# class Suburb(models.Model):
#     name = models.CharField(max_length=200)
#     city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='suburbs')

#     def __str__ (self):
#         return f"{self.name}, {self.city}"

# class Product_location (models.Model):
#     product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="location")
#     city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
#     suburb = models.ForeignKey(Suburb, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

#     def __str__(self) :
#         return f"{self.suburb}, {self.city}"

# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('Pending', 'Pending'),
#         ('Shipped', 'Shipped'),
#         ('Delivered', 'Delivered'),
#     ]
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     order_date = models.DateTimeField(auto_now_add=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     order_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
#     shipping_address = models.TextField()
#     payment_status = models.CharField(max_length=20)
#     updated_at = models.DateTimeField(auto_now=True)
#     id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)
#     id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)


# class Review(models.Model):
#     user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     rating = models.IntegerField()
#     review_text = models.TextField()
#     date = models.DateField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)




