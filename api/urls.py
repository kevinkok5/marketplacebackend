from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView
 

urlpatterns = [
    path("", views.getRoute),
    path('schema/', get_schema_view(title='API Schema', description='Guide for the REST API'), name='api_schema'),
    path('docs/', TemplateView.as_view(
        template_name='static/html/docs.html',
        extra_context={'schema_url':'api/schema'}
        ), name='swagger-ui'),

    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/register/', views.CreateUserAPIView.as_view(), name='register'),
    path('products/create/', views.ProductCreateAPIView.as_view(), name='product-create'),
    path('products/update/<str:pk>', views.ProductUpdateAPIView.as_view(), name='product-update'),
    path('products/', views.ProductListAPIView.as_view(), name='products'), 
    path('products/drafts/',  views.ProductDraftListAPIView.as_view(), name='product-drafts'),
    path('products/drafts/<str:pk>',  views.ProductDraftRetrieveAPIView.as_view(), name='product-drafts'), 
 
]