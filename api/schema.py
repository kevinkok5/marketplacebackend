from django.shortcuts import get_object_or_404
from graphene.relay import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.fields import DjangoConnectionField
from django.db import models

# from graphene_file_upload.scalars import Upload
# from .serializers import ProductSerializer, MediaSerializer
# from .models import Product, Media
from graphene_django.types import DjangoObjectType
# from graphql import GraphQLError
import json
# from .views import  APIException


from graphql import GraphQLError





import graphene
from users import schema as user_schema
from users import models as user_model
from product import schema as product_schema
from product import models as product_model
from product import serializers as product_serializers


from graphql_auth.schema import UserQuery, MeQuery
from graphql_auth import mutations

# class AuthMutation(graphene.ObjectType):
#     register = mutations.Register.Field()
#     verify_account = mutations.VerifyAccount.Field()
#     resend_activation_email = mutations.ResendActivationEmail.Field()
#     send_password_reset_email = mutations.SendPasswordResetEmail.Field()
#     password_reset = mutations.PasswordReset.Field()
#     password_set = mutations.PasswordSet.Field() # For passwordless registration
#     password_change = mutations.PasswordChange.Field()
#     update_account = mutations.UpdateAccount.Field()
#     archive_account = mutations.ArchiveAccount.Field()
#     delete_account = mutations.DeleteAccount.Field()
#     send_secondary_email_activation =  mutations.SendSecondaryEmailActivation.Field()
#     verify_secondary_email = mutations.VerifySecondaryEmail.Field()
#     swap_emails = mutations.SwapEmails.Field()
#     remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

#     # django-graphql-jwt inheritances
#     token_auth = mutations.ObtainJSONWebToken.Field()
#     verify_token = mutations.VerifyToken.Field()
#     refresh_token = mutations.RefreshToken.Field()
#     revoke_token = mutations.RevokeToken.Field()


class Query(user_schema.MeQuery, graphene.ObjectType):
    all_users = DjangoFilterConnectionField(user_schema.UserType)
    user = graphene.Field(user_schema.UserType, id=graphene.ID(required=True))  # global ID is passed

    all_item_categories = DjangoFilterConnectionField(product_schema.ItemCategoryType)
    item_category = graphene.Field(product_schema.ItemCategoryType, id=graphene.ID(required=True))  # global ID is passed
    all_vehicle_categories = DjangoFilterConnectionField(product_schema.VehicleCategoryType)
    vehicle_category = graphene.Field(product_schema.VehicleCategoryType, id=graphene.ID(required=True))  # global ID is passed
    all_house_categories = DjangoFilterConnectionField(product_schema.HouseCategoryType)
    house_category = graphene.Field(product_schema.HouseCategoryType, id=graphene.ID(required=True))  # global ID is passed

    # me = graphene.Field(user_schema.MeType)  # global ID is passed
    # all_products = graphene.List(product_schema.ProductUnion)
    all_products = graphene.Field(
        product_schema.ProductConnection,
        first=graphene.Int(),
        after=graphene.String(),
        product_type=graphene.String(),  # Add this argument
        **{key: graphene.String() for key in ['name', 'make', 'model', 'condition', 'product_status']},
        **{key: graphene.Float() for key in ['price_min', 'price_max']}
    )
    
    user_products = graphene.Field(
        product_schema.ProductConnection,
        first=graphene.Int(),
        after=graphene.String(),
        product_type=graphene.String(),  # Add this argument
        **{key: graphene.String() for key in ['name', 'make', 'model', 'condition', 'product_status']},
        **{key: graphene.Float() for key in ['price_min', 'price_max']}
    )

    # all_products = DjangoFilterConnectionField(product_schema.ProductConnection)



    product = graphene.Field(
        product_schema.ProductUnion,
        id=graphene.ID(required=True),
    )
    all_medias = DjangoFilterConnectionField(product_schema.ProductMediasType)
    # all_Houses = DjangoFilterConnectionField(product_schema.HouseType)
    # all_Items = DjangoFilterConnectionField(product_schema.ItemType)
    # all_Vehicles = DjangoFilterConnectionField(product_schema.VehicleType)


    def resolve_all_users(root, info, **kwargs):
        return user_schema.User.objects.all()

    def resolve_user(root, info, id):
        # return get_object_or_404(userModel.User, id=id)
        return Node.get_node_from_global_id(info, id, only_type=user_schema.UserType)
    
    def resolve_all_item_categories(root, info, **kwargs):
        return product_model.Item_category.objects.all()
    def resolve_item_category(root, info, id):
        return Node.get_node_from_global_id(info, id, only_type=product_model.Item_category)
    
    def resolve_all_vehicle_categories(root, info, **kwargs):
        return product_model.Vehicle_category.objects.all()
    def resolve_vehicle_category(root, info, id):
        return Node.get_node_from_global_id(info, id, only_type=product_model.Vehicle_category)
    
    def resolve_all_house_categories(root, info, **kwargs):
        return product_model.House_category.objects.all()
    def resolve_house_category(root, info, id):
        return Node.get_node_from_global_id(info, id, only_type=product_model.House_category)
    
    # def resolve_me(root, info):
    #     if not info.context.user.is_authenticated:
    #         return None
    #     id = info.context.user.id
    #     return get_object_or_404(user_model.User, id=id)
    
    # def resolve_all_products(root, info):
    #     return product_model.Product.productobjects.all()


    def resolve_all_products(self, info, first=None, after=None, product_type=None, **kwargs):
        user = info.context.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return GraphQLError("Unauthorized")

        # Extract filters from kwargs
        status = kwargs.get('product_status')
        price_min = kwargs.get('price_min')
        price_max = kwargs.get('price_max')
        name = kwargs.get('name')
        make = kwargs.get('make')
        model = kwargs.get('model')
        condition = kwargs.get('condition')

        # Start with a polymorphic query based on `type`
        if product_type == "Item":
            products = product_model.Product.objects.instance_of(product_model.Item)
            if name:
                products = products.filter(name__icontains=name)
            if condition:
                products = products.filter(condition=condition)
        elif product_type == "Vehicle":
            products = product_model.Product.objects.instance_of(product_model.Vehicle)
            if make:
                products = products.filter(make__icontains=make)
            if model:
                products = products.filter(model__icontains=model)
            if condition:
                products = products.filter(condition=condition)
        else:  # Query all products if no product_type is specified
            products = product_model.Product.objects.all()

        # Apply permission-based filters
        if user.is_superuser:  # Admins/Superusers can view all products
            pass
        elif user.is_authenticated:  # Regular authenticated users
            products = products.filter(
                # models.Q(owner=user) | 
                models.Q(product_status="published")
            )

        # Apply common filters
        if status:
            products = products.filter(product_status=status)
        if price_min is not None:
            products = products.filter(price__gte=price_min)
        if price_max is not None:
            products = products.filter(price__lte=price_max)

        # Prefetch related data for efficiency
        products = products.prefetch_related('owner', 'category')

        # Pagination logic
        start_index = 0
        if after:
            start_index = int(after)

        end_index = start_index + first if first else len(products)
        paginated_results = products[start_index:end_index]

        # Create edges for paginated results
        edges = [
            product_schema.ProductEdge(node=item, cursor=str(index))
            for index, item in enumerate(paginated_results, start=start_index)
        ]

        # Construct PageInfo
        page_info = graphene.relay.PageInfo(
            has_next_page=end_index < products.count(),
            has_previous_page=start_index > 0,
            start_cursor=str(start_index) if edges else None,
            end_cursor=str(end_index - 1) if edges else None,
        )

        return product_schema.ProductConnection(edges=edges, page_info=page_info)



    def resolve_user_products(self, info, first=None, after=None, product_type=None, **kwargs):
        user = info.context.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return GraphQLError("Unauthorized")

        # Extract filters from kwargs
        status = kwargs.get('product_status')
        price_min = kwargs.get('price_min')
        price_max = kwargs.get('price_max')
        name = kwargs.get('name')
        make = kwargs.get('make')
        model = kwargs.get('model')
        condition = kwargs.get('condition')

        # Start with products owned by the user
        products = product_model.Product.objects.filter(owner=user)

        # Start with a polymorphic query based on `type`
        if product_type == "Item":
            products = products.instance_of(product_model.Item)
            if name:
                products = products.filter(name__icontains=name)
            if condition:
                products = products.filter(condition=condition)
        elif product_type == "Vehicle":
            products = products.instance_of(product_model.Vehicle)
            if make:
                products = products.filter(make__icontains=make)
            if model:
                products = products.filter(model__icontains=model)
            if condition:
                products = products.filter(condition=condition)

        # Apply common filters
        if status:
            products = products.filter(product_status=status)
        if price_min is not None:
            products = products.filter(price__gte=price_min)
        if price_max is not None:
            products = products.filter(price__lte=price_max)

        # Prefetch related data for efficiency
        products = products.prefetch_related('owner', 'category')

        # Pagination logic
        start_index = 0
        if after:
            start_index = int(after)

        end_index = start_index + first if first else len(products)
        paginated_results = products[start_index:end_index]

        # Create edges for paginated results
        edges = [
            product_schema.ProductEdge(node=item, cursor=str(index))
            for index, item in enumerate(paginated_results, start=start_index)
        ]

        # Construct PageInfo
        page_info = graphene.relay.PageInfo(
            has_next_page=end_index < products.count(),
            has_previous_page=start_index > 0,
            start_cursor=str(start_index) if edges else None,
            end_cursor=str(end_index - 1) if edges else None,
        )

        return product_schema.ProductConnection(edges=edges, page_info=page_info)


        
    
    def resolve_product(self, info, id):
        user = info.context.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            raise GraphQLError("Unauthorized")

        # Decode the global ID
        try:
            type_name, db_id = Node.resolve_global_id(info, id)
            print(f"type_name: {type_name} db_id: {db_id}")
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")

        # Resolve the instance based on the type name
        product = None
        if type_name == "ItemType":
            product = product_model.Item.objects.get(id=db_id)
        elif type_name == "VehicleType":
            product = product_model.Vehicle.objects.get(id=db_id)
        elif type_name == "HouseType":
            product = product_model.House.objects.get(id=db_id)
        else:
            raise ValueError("Invalid type for ProductUnion.")

        # Apply permission checks
        if product.product_status == "published":
            return product  # Published products are viewable by anyone

        if product.owner == user:
            return product  # Owners can view their own products regardless of status

        # Deny access if the user is neither the owner nor the product is published
        raise GraphQLError("You do not have permission to view this product.")









#     import graphene
# from graphene_file_upload.scalars import Upload
# from django.db import transaction
# from .models import Product, Media, Tag, Category
# from .serializers import ProductSerializer, MediaSerializer

# class MediaInput(graphene.InputObjectType):
#     id = graphene.UUID(required=False)
#     media = graphene.String(required=False)
#     # file = Upload(required=False)




# class MediaInput(graphene.InputObjectType):
#     media = Upload(required=True)

# class TagInput(graphene.InputObjectType):
#     name = graphene.String()



# class CreateProductMutation(graphene.Mutation):
#     class Arguments:
#         name = graphene.String()
#         description = graphene.String()
#         price = graphene.Decimal()
#         quantity_available = graphene.Int()
#         category_id = graphene.UUID()
#         status = graphene.Boolean(required=True)
#         # tags = graphene.List(TagInput)
#         medias = graphene.List(MediaInput)

#     product = graphene.Field(product_schema.ProductConnection)

#     error = graphene.List(graphene.String)
    
#     def mutate(root, info, **kwargs):
#         user = info.context.user
#         status = kwargs['status']
#         kwargs['category'] = kwargs.pop('category_id')

#         media_files = kwargs.pop('medias', [])
#         serializer = ProductSerializer(data=kwargs)
#         serializer.is_valid(raise_exception=True)
#         serializer_fields = list(serializer.fields.keys())
#         requiried_fields = ["name", "price", "category"]

#         price = serializer.validated_data.get('price')
#         if price < 0:
#             return GraphQLError("Price must be greater than 0")
    
#         category_id = serializer.validated_data.get('category').id
#         if category_id:
#             try:
#                 category = Category.objects.get(id=category_id)
#             except Category.DoesNotExist:
#                 return GraphQLError("Category does not exist")
        
#         if status:
#             errors = {}
#             for field in serializer_fields:
#                 if field in requiried_fields and not serializer.validated_data.get(field):
#                     errors[field] = "Field is required"
            
#             if errors:
#                 return CreateProductMutation(product=None, error=[str(f'{error}: {errors[error]}') for error in errors])
            
#             product = serializer.save()
            
#             for media_data in media_files:
#                 media_serializer = MediaSerializer(data=media_data)
#                 media_serializer.is_valid(raise_exception=True)
#                 media_serializer.save(product=product)
                
#             return CreateProductMutation(product=product, error=None)
        
#         else:
#             product = serializer.save()
            
#             for media_data in media_files:
#                 media_serializer = MediaSerializer(data=media_data)
#                 media_serializer.is_valid(raise_exception=True)
#                 media_serializer.save(product=product)
            
#             return CreateProductMutation(product=product, error=None)




# class UpdateProductMutation(graphene.Mutation):
#     class Arguments:
#         id = graphene.UUID(required=True)
#         name = graphene.String()
#         description = graphene.String()
#         price = graphene.Decimal()
#         quantity_available = graphene.Int()
#         category_id = graphene.UUID()
#         status = graphene.Boolean(required=True)
#         tags = graphene.List(TagInput)
#         medias = graphene.List(MediaInput)

#     product = graphene.Field(ProductType)
#     error = graphene.List(graphene.String)

#     def mutate(root, info, **kwargs):
#         try:
#             instance = Product.objects.get(id=kwargs["id"])
#             user = info.context.user
#             kwargs['category'] = kwargs.pop('category_id')
#             status = kwargs["status"]

#             media_inputs = kwargs.pop('medias', [])
#             serializer = ProductSerializer(instance, data=kwargs, partial=True)

#             serializer.is_valid(raise_exception=True)
#             serializer_fields = list(serializer.fields.keys())

#             required_fields = ["name", "price", "category"]

#             price = serializer.validated_data.get('price')
#             if price < 0:
#                 return GraphQLError("Price must be greater than 0")

#             category_id = serializer.validated_data.get('category').id
#             if category_id:
#                 try:
#                     category = Category.objects.get(id=category_id)
#                 except Category.DoesNotExist:
#                     return GraphQLError("Category does not exist")

#             if status:
#                 errors = {}
#                 for field in serializer_fields:
#                     if field in required_fields and not serializer.validated_data.get(field):
#                         errors[field] = "Field is required"

#                 if errors:
#                     return UpdateProductMutation(product=None, error=[str(f'{error}: {errors[error]}') for error in errors])

#                 with transaction.atomic():
#                     product = serializer.save()

#                     # Handle media files and URLs
#                     existing_media_ids = [media_data['id'] for media_data in media_inputs if 'id' in media_data]
#                     Media.objects.filter(product=product).exclude(id__in=existing_media_ids).delete()

#                     for media_data in media_inputs:
#                         media_id = media_data.get('id', None)
#                         if media_id:
#                             media_instance = Media.objects.get(id=media_id)
#                             if 'file' in media_data and media_data['file'] is not None:
#                                 media_serializer = MediaSerializer(media_instance, data={'media': media_data['file']}, partial=True)
#                             else:
#                                 media_serializer = MediaSerializer(media_instance, data={'media': media_data['media']}, partial=True)
#                             media_serializer.is_valid(raise_exception=True)
#                             media_serializer.save()
#                         elif 'file' in media_data and media_data['file'] is not None:
#                             media_serializer = MediaSerializer(data={'product': product.id, 'media': media_data['file']})
#                             media_serializer.is_valid(raise_exception=True)
#                             media_serializer.save()

#                 return UpdateProductMutation(product=product, error=None)
#             else:
#                 product = serializer.save()
#                 return UpdateProductMutation(product=product, error=None)
#         except Exception as e:
#             return UpdateProductMutation(product=None, error=[str(e)])




class Mutation(user_schema.AuthMutations, graphene.ObjectType):
    create_product = product_schema.CreateProduct.Field()
    update_product = product_schema.UpdateProduct.Field()
    delete_product = product_schema.DeleteProduct.Field()


schema = graphene.Schema(query=Query, mutation=Mutation) 