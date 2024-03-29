from rest_framework import serializers
from .models import Product, Product_category, Product_tag, Delivery_method, Parent_category

class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_tag
        fields = ['id', 'name']

class DeliveryMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery_method
        fields = ['id', 'method']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_category
        fields = ['id', 'name']

class ParentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent_category
        fields = ['id', 'name']

# class CitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = City
#         fields = ['id', 'name']

# class SuburbSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Suburb
#         fields = ['id', 'name', 'city']

# class ProductLocationSerializer(serializers.ModelSerializer):
#     suburb = SuburbSerializer()

#     class Meta:
#         model = Product_location
#         fields = ['id', 'city', 'suburb']

class ProductSerializer(serializers.ModelSerializer):
    tags = ProductTagSerializer(many=True)
    delivery_method = DeliveryMethodSerializer(many=True)
    category = ProductCategorySerializer()
    # location = ProductLocationSerializer()

    class Meta:
        model = Product
        fields = ['id', 'owner', 'name', 'description', 'price', 'quantity_available', 'category', 'availability_status', 'tags', 'delivery_method', 'condition', 'latitude', 'longitude', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        delivery_method_data = validated_data.pop('delivery_method')
        category_data = validated_data.pop('category')
        # location_data = validated_data.pop('location')
        
        tags = [Product_tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data]
        delivery_methods = [Delivery_method.objects.get_or_create(**method_data)[0] for method_data in delivery_method_data]
        category = Product_category.objects.get_or_create(**category_data)[0]
        # location = Product_location.objects.create(**location_data)
        
        product = Product.objects.create(category=category,  **validated_data)
        product.tags.set(tags)
        product.delivery_method.set(delivery_methods)
        return product
