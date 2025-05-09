from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from users.serializers import CreateUserSerializer
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView
from store.models import Product
# from product.serializers import ProductSerializer
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from store.models import Store
from graphene.relay import Node
from graphql import GraphQLError

from graphene_django.views import GraphQLView as BaseGraphQLView
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from graphene_file_upload.django import FileUploadGraphQLView




class GraphQLView(FileUploadGraphQLView):
    @staticmethod
    def format_error(error):
        formatted_error = super(GraphQLView, GraphQLView).format_error(error)
        print("error: ", error)

        try:
            formatted_error["message"] = str(error)
            
            # Ensure extensions from GraphQLError are included
            if isinstance(error, GraphQLError) and error.extensions:
                formatted_error["extensions"] = error.extensions
            elif hasattr(error, "original_error") and error.original_error:
                formatted_error["extensions"] = {
                    "code": getattr(error.original_error, "code", "INTERNAL_SERVER_ERROR"),
                    "details": str(error.original_error),
                }
        except Exception as e:
            formatted_error["message"] = f"An error occurred while formatting: {e}"

        return formatted_error

    def get_context(self, request):

        # Call the parent method to get the default context
        context = super().get_context(request)
        context.store = None

        # Retrieve store model and header name from settings
        store_model_path = getattr(settings, "GRAPHQL_STORE_MODEL", None)
        store_id_header = getattr(settings, "GRAPHQL_STORE_ID_HEADER", "x-store-id")

        if not store_model_path:
            raise ImproperlyConfigured("GRAPHQL_STORE_MODEL setting is not configured.")

        # Dynamically get the Store model
        try:
            store_model = apps.get_model(store_model_path)
        except LookupError:
            raise ImproperlyConfigured(f"Invalid model path: {store_model_path}")
         
        # Extract store ID from the headers
        store_id = request.headers.get(store_id_header)

        # store_id = "U3RvcmVUeXBlOjU4NWM0NzNkLTQwODQtNDExYy04ZGU1LTFkZmI5M2NhZmQ1Ng=="

        # Validate the store and attach it to the context
        # print(
        #     "store_id: ", store_id
        # )
        if store_id:
            # Decode the global ID
            try:
                type_name, db_id = Node.resolve_global_id(request, store_id)
            except Exception as e:
                raise ValueError(f"Invalid ID format: {e}")
            
            try:
              
                store = get_object_or_404(store_model, id=db_id)
                context.store = store
            except Exception:
                context.store = None
        # print("store_id: ", context.store.id)

        return context
    
    


    

# class APIException(Exception):

#     def __init__(self, message, status=None):
#         self.context = {}
#         if status:
#             self.context['status'] = status
#         super().__init__(message)



@api_view(['GET'])
def getRoute(request):
    routes = [
        '/api/token',
        '/api/token/refresh','users/register/',
        'products/create/',
        'products/',
        'products/drafts/',
        'products/drafts/<str:pk>',
    ]
    return Response(routes) 



    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['first_name'] = user.first_name
        # ...

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class= MyTokenObtainPairSerializer


class CreateUserAPIView(APIView):
    user = None

    def post(user, request):
        # print("Creating user: ", request.data)
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Serializer's save method creates the user
            refresh = RefreshToken.for_user(user)
            refresh['username'] = user.username
            refresh['first_name'] = user.first_name
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            return Response(token, status=status.HTTP_201_CREATED)
        else:
            print("Error creating user: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

# class ProductCreateAPIView(APIView):
#     queryset = Product.objects.all()
#     # serializer_class = ProductSerializer
#     parser_classes = [MultiPartParser, FormParser]

#     def get(self, request, *args, **kwargs):
#         data = []
#         categories = Product_category.objects.all()
        
#         return Response(data, status=status.HTTP_200_OK)

#     def post(self, request, format=None):
#         # Deserialize tags data from JSON string
#         # print(request.data)
#         tags_json = request.data.get('tags')
#         tags = json.loads(tags_json) if tags_json else []

#         # Process image files
#         medias_data = []

#         images = request.FILES.getlist('medias') 

#         for file in images:
#             # if key.startswith('medias'):
#             #     file = request.FILES[key]
#                 # Assuming additional data per file might be sent, handle them here
#             medias_data.append({'media': file})

#         print(medias_data)

#         # Combine tags and images with request data
#         request_data = request.data.copy()
#         request_data['tags'] = tags
#         request_data['medias'] = medias_data

#         print(request_data)

#         data_dict = {}
#         for key, value in request_data.lists():
#             if len(value) == 1:
#                 data_dict[key] = value[0]
#             else:
#                 # Handle lists of dictionaries, like tags
#                 if key == 'tags':
#                     data_dict[key] = [{'name': v} for v in value]
#                 else:
#                     data_dict[key] = value

#         print(data_dict)

#         serializer = ProductSerializer(data=data_dict)
#         # print(serializer)
#         serializer.is_valid(raise_exception=True)

        

#         product_status = serializer.validated_data.get("status")
#         serializer_fields = list(serializer.fields.keys())
#         require_fields = ['owner', 'name', 'price', 'category', 'availability_status', 'delivery_method', 'condition', 'latitude', 'medias', 'longitude', 'status']
        
#         if product_status == "published":
#             error = {}

#             for field in serializer_fields:
#                 # error[field] = f"{field} field is required"
#                 if field in require_fields and not serializer.validated_data.get(field):
#                     error[field] = "Field is required"

#                 # return Response({"error": f"{field} field is required"})

#             if error: 
#                 return Response(error, status=status.HTTP_400_BAD_REQUEST)

#             category_data = serializer.validated_data.get('category')
#             print(category_data)
#             try:
#                 if not category_data:
#                     raise Product_category.DoesNotExist
#                 Product_category.objects.get(id=category_data.id) 
#             except Product_category.DoesNotExist:
#                 return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
#             price = serializer.validated_data.get('price')
#             if price and price <= 0:
#                 return Response({'error': 'Price must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

            
#             # Continue with creating the product if data is valid
#             self.perform_create(serializer)
#             # headers = CreateAPIView.get_success_headers(serializer.data)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#         else: 
#             self.perform_create(serializer)
#             # headers = CreateAPIView.get_success_headers(serializer.data)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#     def perform_create(self, serializer):
#         # Additional business logic before saving
#         serializer.save()
        

# class ProductCreateAPIView(APIView):
#     # queryset = Product.objects.all()
#     # serializer_class = ProductSerializer
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, format=None):
#         print(request.data.getlist('tags'))
#         print(request.data)
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         product_status = serializer.validated_data.get("status")
#         serializer_fields = list(serializer.fields.keys())
#         require_fields = ['owner', 'name', 'price', 'category', 'availability_status', 'delivery_method', 'condition', 'latitude', 'medias', 'longitude', 'status']
        
#         if product_status == "published":
#             error = {}

#             for field in serializer_fields:
#                 # error[field] = f"{field} field is required"
#                 if field in require_fields and not serializer.validated_data.get(field):
#                     error[field] = "Field is required"

#                 # return Response({"error": f"{field} field is required"})

#             if error: 
#                 return Response(error, status=status.HTTP_400_BAD_REQUEST)

#             category_data = serializer.validated_data.get('category')
#             print(category_data)
#             try:
#                 if not category_data:
#                     raise Product_category.DoesNotExist
#                 Product_category.objects.get(id=category_data.id) 
#             except Product_category.DoesNotExist:
#                 return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
#             price = serializer.validated_data.get('price')
#             if price and price <= 0:
#                 return Response({'error': 'Price must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

            
#             # Continue with creating the product if data is valid
#             self.perform_create(serializer)
#             headers = self.get_success_headers(serializer.data)
#             return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
#         else: 
#             self.perform_create(serializer)
#             headers = self.get_success_headers(serializer.data)
#             return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# class ProductListAPIView(ListAPIView):
#     queryset = Product.productobjects.all()
#     serializer_class = ProductSerializer

# class ProductDraftListAPIView(ListAPIView):  
#     # permission_classes = [IsAuthenticated] 
#     queryset = Product.objects.filter(status="draft")
#     serializer_class = ProductSerializer

# class ProductDraftRetrieveAPIView(RetrieveAPIView):  
#     # permission_classes = [IsAuthenticated] 
#     queryset = Product.objects.filter(status="draft")
#     serializer_class = ProductSerializer



# class ProductUpdateAPIView(UpdateAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     # lookup_field = 'id'  # Assuming `id` is used as the lookup field.
#     parser_classes = [MultiPartParser, FormParser]

#     def put(self, request, *args, **kwargs):
#         instance = self.get_object()

#         # Deserialize tags data from JSON string
#         tags_json = request.data.get('tags')
#         tags = json.loads(tags_json) if tags_json else []

#         # Process new image files
#         medias_data = []

#         old_medias_json = request.data.get('medias') 
#         old_medias = json.loads(old_medias_json) if old_medias_json else []
#         # for old_media in old_medias:
#         #     medias_data.append(old_media)

#         media_files = request.FILES.getlist('mediaFiles') 
#         for file in media_files:
#             medias_data.append({'media': file})

#         print(medias_data)

#         # Combine existing and new tags and images with request data
#         request_data = request.data.copy()
#         request_data['tags'] = tags
#         request_data['medias'] = medias_data

#         data_dict = {}
#         for key, value in request_data.lists():
#             if len(value) == 1:
#                 data_dict[key] = value[0]
#             else:
#                 if key == 'tags':
#                     data_dict[key] = [{'name': v} for v in value]
#                 else:
#                     data_dict[key] = value

#         serializer = self.get_serializer(instance, data=data_dict, partial=True)
#         serializer.is_valid(raise_exception=True)

#         product_status = serializer.validated_data.get("status")
#         require_fields = ['owner', 'name', 'price', 'category', 'availability_status', 'delivery_method', 'condition', 'latitude', 'medias', 'longitude', 'status']

#         if product_status == "published":
#             error = {}
#             for field in require_fields:
#                 if field in require_fields and not serializer.validated_data.get(field):
#                     error[field] = "Field is required"

#             if error:
#                 return Response(error, status=status.HTTP_400_BAD_REQUEST)

#             category_data = serializer.validated_data.get('category')
#             try:
#                 if not category_data:
#                     raise Product_category.DoesNotExist
#                 Product_category.objects.get(id=category_data.id)
#             except Product_category.DoesNotExist:
#                 return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

#             price = serializer.validated_data.get('price')
#             if price and price <= 0:
#                 return Response({'error': 'Price must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
#             with transaction.atomic():
#                 try:
#                     current_medias = [media['id'] for media in medias_data]
#                     instance.medias.exclude(id__in=current_medias).delete()

#                     self.perform_update(serializer)
#                     return Response(serializer.data, status=status.HTTP_200_OK)
#                 except Exception as e:
#                     transaction.set_rollback(True)
#                     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             self.perform_update(serializer)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#     def perform_update(self, serializer):
#         # Additional business logic before saving
#         serializer.save()