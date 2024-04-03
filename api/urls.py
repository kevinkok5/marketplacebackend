from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("", views.getRoute),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/register/', views.CreateUserAPIView.as_view(), name='register'),
    path('products/create/', views.ProductCreateAPIView.as_view(), name='product-create'),
    path('products/', views.ProductListAPIView.as_view(), name='products'), 
    path('products/drafts/',  views.ProductDraftListAPIView.as_view(), name='product-drafts'),
    path('products/drafts/<str:pk>',  views.ProductDraftRetrieveAPIView.as_view(), name='product-drafts'),

]