from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from users.serializers import CreateUserSerializer
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView
from product.models import Product, Product_category
from product.serializers import ProductSerializer
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
def getRoute(request):
    routes = [
        '/api/token',
        '/api/token/refresh',
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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductCreateAPIView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_status = serializer.validated_data.get("status")
        serializer_fields = list(serializer.fields.keys())
        require_fields = ['owner', 'name', 'price', 'category', 'availability_status', 'delivery_method', 'condition', 'latitude', 'longitude', 'status']
        
        if product_status == "published":
            error = {}

            for field in serializer_fields:
                # error[field] = f"{field} field is required"
                if field in require_fields and not serializer.validated_data.get(field):
                    error[field] = "Field is required"

                # return Response({"error": f"{field} field is required"})

            if error: 
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            category_data = serializer.validated_data.get('category')
            print(category_data)
            try:
                if not category_data:
                    raise Product_category.DoesNotExist
                Product_category.objects.get(id=category_data.id) 
            except Product_category.DoesNotExist:
                return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
            price = serializer.validated_data.get('price')
            if price and price <= 0:
                return Response({'error': 'Price must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

            
            # Continue with creating the product if data is valid
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        else: 
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductListAPIView(ListAPIView):
    queryset = Product.productobjects.all()
    serializer_class = ProductSerializer

class ProductDraftListAPIView(ListAPIView):  
    # permission_classes = [IsAuthenticated] 
    queryset = Product.objects.filter(status="draft")
    serializer_class = ProductSerializer

class ProductDraftRetrieveAPIView(RetrieveAPIView):  
    # permission_classes = [IsAuthenticated] 
    queryset = Product.objects.filter(status="draft")
    serializer_class = ProductSerializer