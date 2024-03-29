from django.db import models
from django.contrib.auth import get_user_model
import uuid


class Parent_category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Product_category(models.Model):
    name = models.CharField(max_length=100)
    parent_category = models.ForeignKey(Parent_category, on_delete=models.PROTECT, related_name = "children_category")

    def __str__(self):
        return self.name
    
class Product_tag(models.Model):
    name = models.CharField(max_length= 100)

    def __str__(self):
        return self.name
    
class Delivery_method(models.Model):
    method = models.CharField(max_length= 100)

    def __str__(self):
        return self.method
    
class Product(models.Model):
    AVAILABILITY_CHOISES = [
        ("List as Single Item", "single_item"),
        ("List as In Sotck", "in_stock"),
    ]

    STATUS_CHOISES = [
        ('Published', 'published'),
        ('Draft', 'draft'),
    ] 

    CONDITIONS_CHOICES = [
        ('New', 'new'),
        ('Used(Like New)', 'used_like_new'),
        ('Used(Good)', 'used_good'),
        ('Used', 'used'),

    ]

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.PositiveIntegerField(null=True, blank=True)
    category = models.ForeignKey(Product_category, on_delete=models.PROTECT, related_name="products")
    availability_status = models.CharField(max_length=30, choices=AVAILABILITY_CHOISES, default="single_item")
    tags = models.ManyToManyField(Product_tag, related_name="tags")
    delivery_method = models.ManyToManyField(Delivery_method, related_name='products')
    # image_url = models.URLField()
    condition = models.CharField(max_length=30, choices=CONDITIONS_CHOICES) 
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True) 
       
    status = models.CharField(max_length=20, choices=STATUS_CHOISES, default='published')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)


    def __str__(self):
        return self.name

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

