from rest_framework import serializers
from .models import Product, Product_category, Product_tag, Parent_category, Media
from django.core.exceptions import ValidationError
from django.db import transaction



class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_tag
        fields = ['id', 'name']

class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'media', 'created_at', 'updated_at']
# class DeliveryMethodSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Delivery_method
#         fields = ['id', 'method']

# class ProductCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product_category
#         fields = ['id', 'name']

# class ParentCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Parent_category
#         fields = ['id', 'name']

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
    medias = ProductMediaSerializer(many=True)
    # category = ProductCategorySerializer()
    # location = ProductLocationSerializer()

    class Meta:
        model = Product
        fields = ['id', 'owner', 'name', 'description', 'price', 'category', 'availability_status', 'tags', 'medias', 'delivery_method', 'condition', 'latitude', 'longitude', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        category_data = validated_data.pop('category')
        media_data = validated_data.pop('medias')

        with transaction.atomic():
            try:
        
                tags = [Product_tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data]
                category = Product_category.objects.get(id=category_data.id) if category_data else None

                # print(category)
                
                product = Product.objects.create(category=category,  **validated_data)
                product.tags.set(tags)
                medias = [Media.objects.create(product=product, **media_data) for media_data in media_data]

            except Exception as e:
                transaction.set_rollback(True)
                raise serializers.ValidationError({"error": str(e)})


        return product
    
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        media_data = validated_data.pop('medias', None)

        with transaction.atomic():
            try:
                # Update the instance fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                # Update or create tags
                if tags_data is not None:
                    current_tags = [tag['name'] for tag in tags_data]
                    instance.tags.exclude(name__in=current_tags).delete()
                    for tag_data in tags_data:
                        tag_obj, created = Product_tag.objects.get_or_create(**tag_data)
                        if not instance.tags.filter(id=tag_obj.id).exists():
                            instance.tags.add(tag_obj)

                # Update or create media
                if media_data is not None:
                    for media_item in media_data:
                        media_id = media_item.get('id', None)
                        if media_id:
                            media_obj = Media.objects.get(id=media_id, product=instance)
                            for key, value in media_item.items():
                                setattr(media_obj, key, value)
                            media_obj.save()
                        else:
                            Media.objects.create(product=instance, **media_item)

            except Exception as e:
                transaction.set_rollback(True)
                raise serializers.ValidationError({"error": str(e)})

        return instance
