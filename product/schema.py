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
from .models import Product, Item, Vehicle, House, Media, Item_category, Vehicle_category, House_category, Product_tag
import logging
import json
from graphql import GraphQLError


import base64
from .serializers import ItemProductSerializer
from api.views import APIException

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

class ProductInterface(graphene.Interface):
    
    price = graphene.Float()
    product_status = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


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





# -------------------------------------Mutations--------------------------------
class CreateProduct(graphene.Mutation):
    class Arguments:
        product_type = graphene.String(required=True)  # 'item', 'vehicle', 'house'
        product_status = graphene.String(required=True)  # 'item', 'vehicle', 'house'
        product_data = graphene.String(required=True)  # JSON as a string

    product = graphene.Field(ProductUnion)
    error = graphene.List(graphene.String)


    def mutate(self, info, product_type, product_status, product_data):
        user = info.context.user
        # print("user: ", user)
        if not user.is_authenticated:
            return APIException("Authentication required.", status=401)

        # Parse product_data JSON string into a dictionary
        try:
            product_data = json.loads(product_data)
        except json.JSONDecodeError as e:
            return APIException(f"Invalid JSON input: {str(e)}", status=400)
        

        product_data['owner'] = user.id
        # product_data['product_type'] = product_type
        product_data['product_status'] = product_status
        global_category_id = product_data.pop('category_id', None)

        # print("type: ", type(global_category_id))

        serializer = None
        requiried_fields = []
        productCategoryObj = None

        if global_category_id:
            if not isinstance(global_category_id, dict):
                raise APIException('Invalid category. Expected a dictionary with id', status=400)
            
            type_name, db_id = Node.resolve_global_id(info, global_category_id.get('id'))
            product_data['category'] = db_id

        if product_type.capitalize() == 'Item':
            productCategoryObj = Item_category
            product_data['item_condition'] = product_data.pop('condition', None)
            serializer = ItemProductSerializer(data=product_data)
            requiried_fields = ["name", "price", "category"]

        elif product_type.capitalize() == 'Vehicle':
            productCategoryObj = Vehicle_category
            product_data['vehicle_condition'] = product_data.pop('condition', None)
            serializer = ItemProductSerializer(data=product_data)
            requiried_fields = ["make", "model", "model", "year", "price", "category"]

        # elif product_type == 'house':
        else:
            raise APIException("Invalid product type.", status=400)

        if not serializer: 
            raise APIException("Invalid product type.", status=400)
        
        if not productCategoryObj: 
            raise APIException("Invalid product type.", status=400)

        # media_files = kwargs.pop('medias', [])
        
        serializer.is_valid(raise_exception=True)
       
                
        serializer_fields = list(serializer.fields.keys())
        # print("serializer_fields: ", serializer_fields)

        price = serializer.validated_data.get('price')
        if price and price < 0:
            return APIException("Price must be greater than 0", status=400)
    
        category_id = serializer.validated_data.get('category')
        if category_id:
            try:
                category = productCategoryObj.objects.get(id=category_id.id)
            except productCategoryObj.DoesNotExist:
                return APIException("Category does not exist", status=404)
            
        _status = serializer.validated_data.get('product_status')
        print("status: ", _status)


        if _status and _status.capitalize() == "Published":
            print("working")


            # Handle tags and other fields
            # tags = product_data.pop('tags', [])
            product = None
            # print("product_status: ", product_status)

            
            errors = {}
            for field in serializer_fields:
                if field in requiried_fields and not serializer.validated_data.get(field):
                    errors[field] = "Field is required"
            
            if errors:
                return APIException([str(f'{error}: {errors[error]}') for error in errors], status=400)

            # if product_type == 'item':
                               
                # product = serializer.save()

                # product = Item.objects.create(owner=user, **product_data)
            # elif product_type == 'vehicle':
            #     requiried_fields = ["name", "price", "category"]
            #     category_id = serializer.validated_data.get('category').id
            #     if category_id:
            #         try:
            #             category = Category.objects.get(id=category_id)
            #         except Category.DoesNotExist:
            #             return GraphQLError("Category does not exist")


            #     # product = Vehicle.objects.create(owner=user, **product_data)
            # elif product_type == 'house':
            #     requiried_fields = ["name", "price", "category"]
            #     category_id = serializer.validated_data.get('category').id
            #     if category_id:
            #         try:
            #             category = Category.objects.get(id=category_id)
            #         except Category.DoesNotExist:
            #             return GraphQLError("Category does not exist")
            

                # for media_data in media_files:
                #     media_serializer = MediaSerializer(data=media_data)
                #     media_serializer.is_valid(raise_exception=True)
                #     media_serializer.save(product=product)


                # product = House.objects.create(owner=user, **product_data)
            # else:
            #     raise Exception("Invalid product type.")

            # Set tags
            # product.tags.set(tags)
            product = serializer.save()
            return CreateProduct(product=product)
        
        elif _status and _status.capitalize() == "Draft":
            # product = None
            product = serializer.save()

            return CreateProduct(product=product)
        
        else: 
            return APIException("Invalid product status.", status=400)

    

class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)  # Global ID of the product
        # product_type = graphene.String(required=True)  # 'item', 'vehicle', 'house'
        product_status = graphene.String(required=True)  # 'item', 'vehicle', 'house'
        product_data = graphene.String(required=True)  # JSON as a string

    product = graphene.Field(ProductUnion)

    def mutate(self, info, id, product_status,  product_data):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required.")

        # Retrieve the product instance using ProductUnion
        try:
            product_type_name, db_id = Node.resolve_global_id(info, id)
            print(f"type_name: {product_type_name} db_id: {db_id}" )
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")
        
        try: 
            instance = Product.objects.get(id=db_id)
        except Product.DoesNotExist:
            return GraphQLError("Product does not exist.")
        



        if instance.owner != user:
            raise Exception("You are not authorized to update this product.")
        
        try:
            product_data = json.loads(product_data)
        except json.JSONDecodeError as e:
            return GraphQLError(f"Invalid JSON input: {str(e)}")
        

        # print("product_status: ", product_status)
        product_data['product_status'] = product_status
        # print("work well so far")


        global_category_id = product_data.pop('category_id', None)



        serializer = None
        requiried_fields = []
        productCategoryObj = None



        if global_category_id:
            category_type_name, db_id = Node.resolve_global_id(info, global_category_id.get('id'))
            product_data['category'] = db_id

        print("type_name: ", product_type_name)

        if product_type_name == "ItemType":
            productCategoryObj = Item_category
            product_data['item_condition'] = product_data.pop('condition', None)
            serializer = ItemProductSerializer(instance, data=product_data, partial=True)
            requiried_fields = ["name", "price", "category"]

        elif product_type_name == "VehicleType":
            productCategoryObj = Vehicle_category
            product_data['vehicle_condition'] = product_data.pop('condition', None)
            serializer = ItemProductSerializer(instance, data=product_data, partial=True)
            requiried_fields = ["make", "model", "model", "year", "price", "category"]
        # elif type_name == "HouseType":

        else:
            raise Exception("Invalid product type.")

        if not serializer: 
            return GraphQLError("Invalid product type.")
        
        if not productCategoryObj: 
            return GraphQLError("Product has no category.")

        # media_files = kwargs.pop('medias', [])
        
        serializer.is_valid(raise_exception=True)

        serializer_fields = list(serializer.fields.keys())
        # print("serializer_fields: ", serializer_fields)

        price = serializer.validated_data.get('price')
        if price and price < 0:
            return GraphQLError("Price must be greater than 0")
    
        category_id = serializer.validated_data.get('category')
        # print("category_id: ", category_id)

        if category_id and category_id:
            try:
                category = productCategoryObj.objects.get(id=category_id.id)
            except productCategoryObj.DoesNotExist:
                return GraphQLError("Category does not exist")
            
            _status = serializer.validated_data.get('product_status')

        if _status and _status.capitalize() == "Published":


            # Handle tags and other fields
            # tags = product_data.pop('tags', [])
            product = None

            errors = {}
            for field in serializer_fields:
                if field in requiried_fields and not (serializer.validated_data.get(field) or getattr(instance, field, None)):
                    errors[field] = "Field is required"
            
            if errors:
                return GraphQLError([str(f'{error}: {errors[error]}') for error in errors])
            
            product = serializer.save()
            return CreateProduct(product=product)
            
        elif _status and _status.capitalize() == "Draft":
            # product = None
            product = serializer.save()

            return CreateProduct(product=product)
        
        else: 
            return graphene.MutationError("Couldn't update product.")

        # # Update product fields dynamically
        # tags = product_data.pop('tags', None)
        # for key, value in product_data.items():
        #     if hasattr(product, key):
        #         setattr(product, key, value)

        # if tags is not None:
        #     product.tags.set(tags)

        # product.save()
        # return UpdateProduct(product=product)



class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)  # Global ID of the product

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return GraphQLError("Authentication required.")

        # Retrieve the product instance using ProductUnion
        try:
            type_name, db_id = Node.resolve_global_id(info, id)
            # print(f"type_name: {type_name} db_id: {db_id}" )
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")
        
        try: 
            product = Product.objects.get(id=db_id)
        except Product.DoesNotExist:
            return APIException("Product does not exist.", status=404)

        if product.owner != user:
            return APIException("You are not authorized to delete this product.", status=403)

        product.delete()
        return DeleteProduct(success=True)




