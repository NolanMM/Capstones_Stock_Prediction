from rest_framework import serializers
from .models import StockPrice, Article, Profile, PortfolioItem
from django.contrib.auth.models import User
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = ['Date', 'Close_Prices', 'High_Prices', 'Low_Prices', 'Open_Prices', 'Volume', 'Stock_Symbol']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['profile_picture_url']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'password']
        extra_kwargs = {
            # Ensure password is not sent back in responses
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        profile = instance.profile

        # Update user fields
        for field in ['email', 'first_name', 'last_name']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        
        if password:
            instance.set_password(password)
            
        instance.save()

        # Update profile
        if profile_data:
            profile.profile_picture_url = profile_data.get('profile_picture_url', profile.profile_picture_url)
            profile.save()

        return instance

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 're_password')

class PortfolioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ['id', 'stock_symbol']