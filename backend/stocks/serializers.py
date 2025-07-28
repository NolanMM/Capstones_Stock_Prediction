from rest_framework import serializers
from .models import StockPrice, Article, Profile, PortfolioItem
from django.contrib.auth.models import User
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

class CustomUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 're_password', 'first_name', 'last_name')

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
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        is_active = validated_data.pop('is_active', False)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            is_active=is_active
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
    

class CustomUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        """
        Overrides the default behavior to ensure the user is created as inactive,
        pending email verification.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            is_active=False
        )
        return user

class PortfolioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ['id', 'stock_symbol']

class HistoricalStockNewsSerializer(serializers.Serializer):
    """
    Serializer for the Historical_Stock_News_Sentiment_Score table.
    This acts as a Data Transfer Object (DTO) for the news data.
    """
    id = serializers.IntegerField(read_only=True)
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    datetime = serializers.CharField()
    headline = serializers.CharField()
    image = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    related = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    symbol = serializers.CharField()
    positive_value = serializers.FloatField(required=False, allow_null=True)
    negative_value = serializers.FloatField(required=False, allow_null=True)
    neutral_value = serializers.FloatField(required=False, allow_null=True)