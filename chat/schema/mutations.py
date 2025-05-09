import graphene
from graphene.relay import Node
# from .types import ProductUnion, ProductType, ItemType, VehicleType, HouseType, ProductTagstype, ProductMediasType
from ..models import Message, Conversation
# import base64
# from ..serializers import ItemProductSerializer
# # from api.views import APIException
# from graphql import GraphQLError
# from django.contrib.auth.models import Group
from .types import MessageType
# from store.serializers import StoreSerializer
# from store.permissions.decorators import group_shop_owner_permission_required, store_permission_required
# from graphql_jwt.decorators import login_required
from graphene_file_upload.scalars import Upload

# from store.permissions.permissions import user_has_store_permission, user_has_product_permission




# # -------------------------------------Mutations--------------------------------
# class MediaInput(graphene.InputObjectType):
#     id = graphene.UUID()
#     media = Upload()


class SendMessage(graphene.Mutation):
    message = graphene.Field(MessageType)
    success = graphene.Boolean()


    class Arguments:
        conversation_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, conversation_id, content):
        user = info.context.user
        conversation = Conversation.objects.get(pk=conversation_id)
        # Optional: Validate that `user` is a participant in the conversation
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        return SendMessage(message=message, success=True)

class Mutation(graphene.ObjectType):
    send_message = SendMessage.Field()



class MarkMessageDelivered(graphene.Mutation):
    message = graphene.Field(MessageType)
    success = graphene.Boolean()


    class Arguments:
        message_id = graphene.ID(required=True)

    def mutate(self, info, message_id):
        user = info.context.user
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            raise Exception("Message not found")

        # Only the recipient should mark a message as delivered.
        if message.sender == user:
            raise Exception("Cannot mark your own message as delivered.")

        # Only update if status is still "sent"
        if message.status == "sent":
            message.status = "delivered"
            message.save()
        return MarkMessageDelivered(message=message, success=True)

class MarkMessagesAsRead(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        conversation_id = graphene.ID(required=True)

    def mutate(self, info, conversation_id):
        user = info.context.user
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise Exception("Conversation not found")

        if user not in conversation.participants.all():
            raise Exception("Not authorized to update this conversation.")

        # Mark messages from the other user as read
        Message.objects.filter(
            conversation=conversation
        ).exclude(sender=user).filter(status__in=["sent", "delivered"]).update(status="read")
        return MarkMessagesAsRead(success=True)
    


class ChatMutations(graphene.ObjectType):
    mark_message_delivered = MarkMessageDelivered.Field()
    mark_messages_as_read = MarkMessagesAsRead.Field()


# class Mutation(graphene.ObjectType):
#     mark_message_delivered = MarkMessageDelivered.Field()
#     mark_messages_as_read = MarkMessagesAsRead.Field()


# class UpdateStore(graphene.Mutation):
#     store = graphene.Field(StoreType)

#     class Arguments:
#         id = graphene.UUID(required=True)  # Store ID to update
#         name = graphene.String(required=False)
#         description = graphene.String(required=False)
#         # profile_image = Upload(required=False)

#     @store_permission_required("can_edit_store")
#     def mutate(self, info, name=None, description=None, profile_image=None):
#         instance = info.store

#         # Prepare data for the serializer
#         data = {
#             "name": name,
#             "description": description,
#         }

#         # Serialize and save the new store
#         serializer = StoreSerializer(instance, data=data, partial=True)
#         if serializer.is_valid():
#             store = serializer.save()

#             # if profile_image:
#             #     store.profile_image = profile_image
#             #     store.save()
#             return UpdateStore(store=store)
#         else: 
#             raise GraphQLError(f"Invalid input: {serializer.errors}")




# class CreateProduct(graphene.Mutation):
#     class Arguments:
#         product_type = graphene.String(required=True)  # 'item', 'vehicle', 'house'
#         product_status = graphene.String(required=True)  # 'draft', 'published'
#         product_data = graphene.String(required=True)  # JSON as a string
#         product_medias = graphene.List(MediaInput)  

#     product = graphene.Field(ProductUnion)
#     error = graphene.List(graphene.String)


#     def mutate(self, info, product_type, product_status, product_medias, product_data):
#         user = info.context.user
#         store = info.context.store

#         if not user.is_authenticated:
#             return GraphQLError("Authentication required.")
        
#         if store is None:
#             return GraphQLError("No store associated with this request.")
        
#         if not user_has_store_permission(user, store, "can_create_products"):
#             return GraphQLError("You do not have permission to create products. Please check with your administrator")

#         # Parse product_data JSON string into a dictionary
#         try:
#             product_data = json.loads(product_data)
#         except json.JSONDecodeError as e:
#             return GraphQLError(f"Invalid JSON input: {str(e)}")        

#         product_data['store'] = store.id
#         # product_data['product_type'] = product_type
#         product_data['product_status'] = product_status
#         product_data['medias'] = product_medias
#         global_category_id = product_data.pop('category_id', None)

#         # print("type: ", type(global_category_id))

#         serializer = None
#         requiried_fields = []
#         productCategoryObj = None


#         if global_category_id:
#             if not isinstance(global_category_id, dict):
#                 raise GraphQLError('Invalid category. Expected a dictionary with id')
            
#             print("global_category_id: ", global_category_id)
            
#             type_name, db_id = Node.resolve_global_id(info, global_category_id.get('id'))
#             product_data['category'] = db_id

#         if product_type.capitalize() == 'Item':
#             productCategoryObj = Item_category
#             product_data['item_condition'] = product_data.pop('condition', None)
#             serializer = ItemProductSerializer(data=product_data)
#             requiried_fields = ["name", "price", "category"]

#         elif product_type.capitalize() == 'Vehicle':
#             productCategoryObj = Vehicle_category
#             product_data['vehicle_condition'] = product_data.pop('condition', None)
#             serializer = ItemProductSerializer(data=product_data)
#             requiried_fields = ["make", "model", "model", "year", "price", "category"]

#         # elif product_type == 'house':
#         else:
#             raise GraphQLError("Invalid product type")

#         if not serializer: 
#             raise GraphQLError("Invalid product type")
        
#         if not productCategoryObj: 
#             raise GraphQLError("Invalid product type")

#         # media_files = kwargs.pop('medias', [])
        

        
#         serializer.is_valid(raise_exception=True)
#         print("working until here..")
                
#         serializer_fields = list(serializer.fields.keys())
#         # print("serializer_fields: ", serializer_fields)

#         price = serializer.validated_data.get('price')
#         if price and price < 0:
#             return GraphQLError("Price must be greater than 0")
    
#         category_id = serializer.validated_data.get('category')
#         if category_id:
#             try:
#                 category = productCategoryObj.objects.get(id=category_id.id)
#             except productCategoryObj.DoesNotExist:
#                 return GraphQLError("Category does not exist")
            
#         _status = serializer.validated_data.get('product_status')
#         print("status: ", _status)


#         if _status and _status.capitalize() == "Published":
#             print("working")


#             # Handle tags and other fields
#             # tags = product_data.pop('tags', [])
#             product = None
#             # print("product_status: ", product_status)

            
#             errors = {}
#             for field in serializer_fields:
#                 if field in requiried_fields and not serializer.validated_data.get(field):
#                     errors[field] = "Field is required"
            
#             if errors:
#                 return GraphQLError([str(f'{error}: {errors[error]}') for error in errors])

#             # if product_type == 'item':
                               
#                 # product = serializer.save()

#                 # product = Item.objects.create(owner=user, **product_data)
#             # elif product_type == 'vehicle':
#             #     requiried_fields = ["name", "price", "category"]
#             #     category_id = serializer.validated_data.get('category').id
#             #     if category_id:
#             #         try:
#             #             category = Category.objects.get(id=category_id)
#             #         except Category.DoesNotExist:
#             #             return GraphQLError("Category does not exist")


#             #     # product = Vehicle.objects.create(owner=user, **product_data)
#             # elif product_type == 'house':
#             #     requiried_fields = ["name", "price", "category"]
#             #     category_id = serializer.validated_data.get('category').id
#             #     if category_id:
#             #         try:
#             #             category = Category.objects.get(id=category_id)
#             #         except Category.DoesNotExist:
#             #             return GraphQLError("Category does not exist")
            

#                 # for media_data in media_files:
#                 #     media_serializer = MediaSerializer(data=media_data)
#                 #     media_serializer.is_valid(raise_exception=True)
#                 #     media_serializer.save(product=product)


#                 # product = House.objects.create(owner=user, **product_data)
#             # else:
#             #     raise Exception("Invalid product type.")

#             # Set tags
#             # product.tags.set(tags)
#             product = serializer.save()
#             return CreateProduct(product=product)
        
#         elif _status and _status.capitalize() == "Draft":
#             # product = None
#             product = serializer.save()

#             return CreateProduct(product=product)
        
#         else: 
#             return GraphQLError("Invalid product status.")

    

# class UpdateProduct(graphene.Mutation):
#     class Arguments:
#         id = graphene.ID(required=True)  # Global ID of the product
#         # product_type = graphene.String(required=True)  # 'item', 'vehicle', 'house'
#         product_status = graphene.String(required=True)  # 'item', 'vehicle', 'house'
#         product_data = graphene.String(required=True)  # JSON as a string
#         product_medias = graphene.List(MediaInput)  


#     product = graphene.Field(ProductUnion)
#     error = graphene.List(graphene.String)


#     def mutate(self, info, id, product_status, product_medias, product_data):
#         user = info.context.user
#         store = info.context.store

#         if not user.is_authenticated:
#             return GraphQLError("Authentication required.")
        
#         if store is None:
#             return GraphQLError("No store associated with this request.")
        
#         if not user_has_store_permission(user, store, "can_edit_products"):
#             return GraphQLError("You do not have permission to Edit this product. Please check with your administrator")


#         # Retrieve the product instance using ProductUnion
#         try:
#             product_type_name, db_id = Node.resolve_global_id(info, id)
#             print(f"type_name: {product_type_name} db_id: {db_id}" )
#         except Exception as e:
#             raise ValueError(f"Invalid ID format: {e}")
        
#         try: 
#             instance = Product.objects.get(id=db_id)
#         except Product.DoesNotExist:
#             return GraphQLError("Product does not exist.")

#         if instance.store != store:
#             raise Exception("You are not authorized to update this product.")
        
#         try:
#             product_data = json.loads(product_data)
#         except json.JSONDecodeError as e:
#             return GraphQLError(f"Invalid JSON input: {str(e)}")
        

#         product_data['product_status'] = product_status
#         product_data['medias'] = product_medias
#         global_category_id = product_data.pop('category_id', None)



#         serializer = None
#         requiried_fields = []
#         productCategoryObj = None



#         if global_category_id:
#             category_type_name, db_id = Node.resolve_global_id(info, global_category_id.get('id'))
#             product_data['category'] = db_id

#         # print("type_name: ", product_type_name)

#         if product_type_name == "ItemType":
#             productCategoryObj = Item_category
#             product_data['item_condition'] = product_data.pop('condition', None)
#             serializer = ItemProductSerializer(instance, data=product_data, partial=True)
#             requiried_fields = ["name", "price", "category"]

#         elif product_type_name == "VehicleType":
#             productCategoryObj = Vehicle_category
#             product_data['vehicle_condition'] = product_data.pop('condition', None)
#             serializer = ItemProductSerializer(instance, data=product_data, partial=True)
#             requiried_fields = ["make", "model", "model", "year", "price", "category"]
#         # elif type_name == "HouseType":

#         else:
#             raise Exception("Invalid product type.")

#         if not serializer: 
#             return GraphQLError("Invalid product type.")
        
#         if not productCategoryObj: 
#             return GraphQLError("Product has no category.")

#         # media_files = kwargs.pop('medias', [])
        
#         serializer.is_valid(raise_exception=True)

#         serializer_fields = list(serializer.fields.keys())
#         # print("serializer_fields: ", serializer_fields)

#         price = serializer.validated_data.get('price')
#         if price and price < 0:
#             return GraphQLError("Price must be greater than 0")
    
#         category_id = serializer.validated_data.get('category')
#         # print("category_id: ", category_id)

#         if category_id and category_id:
#             try:
#                 category = productCategoryObj.objects.get(id=category_id.id)
#             except productCategoryObj.DoesNotExist:
#                 return GraphQLError("Category does not exist")
            
#             _status = serializer.validated_data.get('product_status')

#         if _status and _status.capitalize() == "Published":


#             # Handle tags and other fields
#             # tags = product_data.pop('tags', [])
#             product = None

#             errors = {}
#             for field in serializer_fields:
#                 if field in requiried_fields and not (serializer.validated_data.get(field) or getattr(instance, field, None)):
#                     errors[field] = "Field is required"
            
#             if errors:
#                 return GraphQLError([str(f'{error}: {errors[error]}') for error in errors])
            
#             product = serializer.save()
#             return CreateProduct(product=product)
            
#         elif _status and _status.capitalize() == "Draft":
#             # product = None
#             product = serializer.save()

#             return CreateProduct(product=product)
        
#         else: 
#             return GraphQLError("Invalid product status.")

#         # # Update product fields dynamically
#         # tags = product_data.pop('tags', None)
#         # for key, value in product_data.items():
#         #     if hasattr(product, key):
#         #         setattr(product, key, value)

#         # if tags is not None:
#         #     product.tags.set(tags)

#         # product.save()
#         # return UpdateProduct(product=product)



# class DeleteProduct(graphene.Mutation):
#     class Arguments:
#         id = graphene.ID(required=True)  # Global ID of the product

#     success = graphene.Boolean()

#     def mutate(self, info, id):
#         user = info.context.user
#         store = info.context.store

#         if not user.is_authenticated:
#             return GraphQLError("Authentication required.")
        
#         if store is None:
#             return GraphQLError("No store associated with this request.")
        
#         if not user_has_store_permission(user, store, "can_edit_products"):
#             return GraphQLError("You do not have permission to Edit this product. Please check with your administrator")

#         # Retrieve the product instance using ProductUnion
#         try:
#             type_name, db_id = Node.resolve_global_id(info, id)
#             # print(f"type_name: {type_name} db_id: {db_id}" )
#         except Exception as e:
#             raise ValueError(f"Invalid ID format: {e}")
        
#         try: 
#             product = Product.objects.get(id=db_id)
#         except Product.DoesNotExist:
#             return GraphQLError("Product does not exist.")

#         if product.store != store:
#             return GraphQLError("You are not authorized to delete this product.")

#         product.delete()
#         return DeleteProduct(success=True)




