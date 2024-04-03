from django.contrib import admin
from .models import Product, Parent_category, Product_category, Product_tag

# Register your models here.

admin.site.register(Product)
admin.site.register(Parent_category)
admin.site.register(Product_category)
admin.site.register(Product_tag)
