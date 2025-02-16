# mutation CreateItem {
#   createProduct(
#     productType: "item"
#     productData: """
#     {
#       "price": 10.0,
#       "description": "A new item",
#       "tags": [{"name": "tag1"}, {"name": "tag2"}],
#       "condition": "new",
#       "category_id": {"id": "SXRlbUNhdGVnb3J5VHlwZTox"},
#     	"status": "published"
#     }
#     """
#     productStatus: "draft"
#   ) {
#     product {
#       ... on ItemType {
#         id
#         name
#         price
#         category {
#           name
#           id
#         }
#       }
#     }
#   }
# }





from graphene.relay import Node
from graphene import Union
import graphene
from graphene_django import DjangoObjectType
from ..models import Store, Product, Item, Vehicle, House, Media, Item_category, Vehicle_category, House_category, Product_tag
import logging
import json
from graphql import GraphQLError
from ..permissions.permissions import user_has_store_permission, STORE_PERMISSIONS


import base64
from ..serializers import ItemProductSerializer
# from api.views import APIException

# def from_global_id(global_id):
#     """
#     Decodes a global ID back into its type and ID.
#     """
#     try:
#         decoded_id = base64.b64decode(global_id).decode('utf-8')
#         type_name, id_ = decoded_id.split(':', 1)
#         return type_name, id_
#     except Exception as e:
#         raise ValueError(f"Invalid global ID '{global_id}'. Error: {e}")

# # Usage Example
# global_id = "SXRlbVR5cGU6MGE1ZDllMWUtNzM4Ny00YWI4LTkzYjYtYzhhNzExNzJhMDE3"
# type_name, internal_id = from_global_id(global_id)
# print(f"Type: {type_name}, ID: {internal_id}")

logger = logging.getLogger(__name__)

# class CustomNode(Node):
#     @staticmethod
#     def get_node_from_global_id(info, global_id, only_type=None):
#         type_name, internal_id = from_global_id(global_id)

#         if type_name == "ItemType":
#             return Item.objects.get(pk=internal_id)
#         elif type_name == "VehicleType":
#             return Vehicle.objects.get(pk=internal_id)
#         elif type_name == "HouseType":
#             return House.objects.get(pk=internal_id)

#         raise Exception(f"Cannot resolve type: {type_name}")

class CustomConnection(graphene.Connection):
    success = graphene.Boolean()

    class Meta:
        abstract = True
        
    def resolve_success(root, info):
        # Return True if the connection resolved successfully
        return True  # Customize this logic if needed


class StoreType(DjangoObjectType): 
    permissions = graphene.JSONString()
   
    class Meta: 
        model =  Store
        connection_class = CustomConnection  # Use the custom connection

        interfaces = (Node, )
        fields = "__all__"
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        }

    def resolve_profile_image(self, info):
        if self.profile_image:
            return info.context.build_absolute_uri(self.profile_image.url)
        return None

    
    def resolve_permissions(self, info):
        user = info.context.user
        return {permission: user_has_store_permission(user, self, permission) for permission in STORE_PERMISSIONS}

# class ProductInterface(graphene.Interface):
    
#     price = graphene.Float()
#     product_status = graphene.String()
#     latitude = graphene.Float()
#     longitude = graphene.Float()
#     created_at = graphene.DateTime()
#     updated_at = graphene.DateTime()


class ItemCategoryType(DjangoObjectType):
    class Meta:
        model = Item_category
        interfaces = (Node, )
        fields = "__all__"
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        }

class VehicleCategoryType(DjangoObjectType):
    class Meta:
        model = Vehicle_category
        interfaces = (Node, )
        fields = "__all__"
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        }

class HouseCategoryType(DjangoObjectType):
    class Meta:
        model = House_category
        interfaces = (Node, )
        fields = "__all__"
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        }

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (Node,)

        fields = "__all__"
        filter_fields = {
            'product_status': ['exact'],
            'price': ['exact', 'gt', 'lt'],
            'latitude': ['exact'],
            'longitude': ['exact'],
        }

class ItemType(DjangoObjectType):
    class Meta:
        model = Item
        interfaces = (Node,)
        fields = "__all__"

    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, Item)

class VehicleType(DjangoObjectType):
    class Meta:
        model = Vehicle
        interfaces = (Node, )
        fields = "__all__"
    
    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, Vehicle)
        

class HouseType(DjangoObjectType):
    class Meta:
        model = House
        interfaces = (Node, )
        fields = "__all__"
    
    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, House)

class ProductMediasType(DjangoObjectType):
    class Meta:
        model = Media
        interfaces = (Node,)
        fields = "__all__"
        filter_fields = []
    def resolve_media(self, info):
        if self.media:
            return info.context.build_absolute_uri(self.media.url)
        return None
    
class ProductTagstype(DjangoObjectType):
    class Meta: 
        model = Product_tag
        interfaces = (Node,)
        fields = ["id", "name"]
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        } 


class ProductUnion(Union):
    class Meta:
        types = (ItemType, VehicleType, HouseType)

    @staticmethod
    def resolve_type(instance, info):
        if isinstance(instance, Item):  # Check if it's an Item
            return ItemType
        elif isinstance(instance, Vehicle):  # Check if it's a Vehicle
            return VehicleType
        elif isinstance(instance, House):  # Check if it's a House
            return HouseType
        # return None  # Fallback for unknown types

class ProductEdge(graphene.ObjectType):
    node = graphene.Field(ProductUnion)
    cursor = graphene.String()

class ProductConnection(graphene.ObjectType):
    edges = graphene.List(ProductEdge)
    page_info = graphene.Field(graphene.relay.PageInfo)












