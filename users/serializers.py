from rest_framework import serializers
from django.contrib.auth import get_user_model

class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)  # Add confirm_password field

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'email','username', 'password', 'confirm_password']  # Include confirm_password field
        

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        user = get_user_model().objects.create(
            first_name=validated_data['first_name'],
            username = validated_data['username'],
            email = validated_data['email'],
        )

        user.set_password(validated_data['password'])
        user.save()
        
        return user
