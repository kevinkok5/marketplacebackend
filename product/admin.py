from django.contrib import admin
from .models import Product, Parent_category, Product_category, Product_tag, Media

# Register your models here.

admin.site.register(Product)
admin.site.register(Parent_category)
admin.site.register(Product_category)
admin.site.register(Product_tag)
admin.site.register(Media)
