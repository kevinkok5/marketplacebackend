from django.contrib import admin
from .models import Store, Product, Product_tag, Media, Item, House, Vehicle, Item_category, Vehicle_category, House_category


from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter



class ModelAChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = Product  # Optional, explicitly set here.

    
   


@admin.register(Item)
class ModelBAdmin(ModelAChildAdmin):
    base_model = Item  # Explicitly set here!
    # define custom features here


@admin.register(Vehicle)
class ModelCAdmin(ModelBAdmin):
    base_model = Vehicle  # Explicitly set here!
    show_in_index = True  # makes child model admin visible in main admin site
    # define custom features here

@admin.register(House)
class ModelCAdmin(ModelBAdmin):
    base_model = House  # Explicitly set here!
    show_in_index = True  # makes child model admin visible in main admin site
    # define custom features here


@admin.register(Product)
class ModelAParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = Product  # Optional, explicitly set here.
    child_models = (Item, Vehicle, House)
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.

# Register your models here.

admin.site.register(Product_tag)
admin.site.register(Item_category)
admin.site.register(House_category)
admin.site.register(Vehicle_category)
admin.site.register(Media)
admin.site.register(Store)
