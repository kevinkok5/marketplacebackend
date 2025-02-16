from rest_framework import serializers
from .models import Store, Product, Product_tag, Media, Item_category, Item, Vehicle, Vehicle_category
from django.core.exceptions import ValidationError
from django.db import transaction
# from api.views import APIException
from django.contrib.auth import get_user_model
from graphql import GraphQLError



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





class StoreSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)
    id = serializers.UUIDField(read_only=True)
    # store_status = serializers.ChoiceField(choices=Store.STATUS_CHOISES, required=False)

    class Meta:
        model = Store
        fields = [
            'id', 
            'name', 
            'owner', 
            'description', 
            'profile_image', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'id', 'store_status']

    def create(self, validated_data):
        # Set the owner to the currently authenticated user if not provided
        return super().create(validated_data)

    def update(self, instance, validated_data):
        owner = validated_data.pop('owner', None) # make sure the owner is not updated
        # Update fields if present in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class ItemProductSerializer(serializers.ModelSerializer):
    tags = ProductTagSerializer(many=True)
    medias = ProductMediaSerializer(many=True)
    # category = ProductCategorySerializer()
    # location = ProductLocationSerializer()

    class Meta:
        model = Item
        fields = ['id', 'store', 'name', 'description', 'price', 'category', 'medias', 'availability_status', 'tags', 'delivery_method', 'item_condition', 'latitude', 'longitude', 'product_status']

    def to_internal_value(self, data):
        # Get the defined fields on the serializer
        allowed_fields = set(self.fields.keys())
        incoming_fields = set(data.keys())

        # Find extra fields in the input
        extra_fields = incoming_fields - allowed_fields
        if extra_fields:
            raise GraphQLError(
                {field: f"{field} is not a valid field for Item Products." for field in extra_fields}, 
                # status="HTTP_400_BAD_REQUEST",
                # status=400,
            )

        # Proceed with the normal validation process
        return super().to_internal_value(data)
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        category_data = validated_data.pop('category', None)
        media_data = validated_data.pop('medias', None)

        with transaction.atomic():
            try:
        
                tags = [Product_tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data]
                category = Item_category.objects.get(id=category_data.id) if category_data else None

                # print(category)
                
                item = Item.objects.create(category=category,  **validated_data)
                item.tags.set(tags)
                medias = [Media.objects.create(product=item, **media_data) for media_data in media_data]

            except Exception as e:
                transaction.set_rollback(True)
                raise serializers.ValidationError({"error": str(e)})


        return item
    
    
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
                            if media_obj:
                                for key, value in media_item.items():
                                    setattr(media_obj, key, value)
                                media_obj.save()
                        else:
                            Media.objects.create(product=instance, **media_item)

            except Exception as e:
                transaction.set_rollback(True)
                raise serializers.ValidationError({"error": str(e)})

        return instance
    


class VehicleProductSerializer(serializers.ModelSerializer):
    tags = ProductTagSerializer(many=True)
    # medias = ProductMediaSerializer(many=True)
    # category = ProductCategorySerializer()
    # location = ProductLocationSerializer()

    class Meta:
        model = Vehicle
        fields = ['id', 'model', 'make', 'description', 'price', 'category', 'tags', 'year', 'vehicle_condition', 'latitude', 'longitude', 'product_status']

    def to_internal_value(self, data):
        # Get the defined fields on the serializer
        allowed_fields = set(self.fields.keys())
        incoming_fields = set(data.keys())

        # Find extra fields in the input
        extra_fields = incoming_fields - allowed_fields
        if extra_fields:
            raise GraphQLError(
                {field: f"{field} is not a valid field for Item Products." for field in extra_fields}, 
                # status="HTTP_400_BAD_REQUEST",
            )

        # Proceed with the normal validation process
        return super().to_internal_value(data)
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        category_data = validated_data.pop('category', None)
        media_data = validated_data.pop('medias', None)

        with transaction.atomic():
            try:
        
                tags = [Product_tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data]
                category = Vehicle_category.objects.get(id=category_data.id) if category_data else None

                # print(category)
                
                vehicle = Vehicle.objects.create(category=category,  **validated_data)
                vehicle.tags.set(tags)
                medias = [Media.objects.create(product=vehicle, **media_data) for media_data in media_data]

            except Exception as e:
                transaction.set_rollback(True)
                raise serializers.ValidationError({"error": str(e)})


        return vehicle
    
    
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
