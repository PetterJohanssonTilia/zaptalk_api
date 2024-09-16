from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Movie, UserProfile, Like, Comment
#Needed for cloudinary Avatar
from django.core.files.base import ContentFile
import base64
import logging

logger = logging.getLogger('zaptalk_api.api')

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = fields = ['id', 'title', 'year', 'cast', 'genres', 'href', 'extract', 'thumbnail', 'thumbnail_width', 'thumbnail_height', 'likes_count']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    comment_count = serializers.SerializerMethodField()
    total_likes_received = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'avatar', 'bio', 'location', 'birth_date', 'website', 
                  'comment_count', 'total_likes_received', 'followers_count', 'following_count', 'is_following']

    def get_comment_count(self, obj):
        return obj.get_comment_count()

    def get_total_likes_received(self, obj):
        return obj.get_total_likes_received()

    def get_followers_count(self, obj):
        return obj.get_followers_count()

    def get_following_count(self, obj):
        return obj.get_following_count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.userprofile in obj.followers.all()
        return False

    def update(self, instance, validated_data):
        logger.info(f"Updating profile for user: {instance.user.username}")
        logger.info(f"Validated data: {validated_data}")
        
        avatar = validated_data.pop('avatar', None)
        if avatar:
            logger.info(f"Updating avatar: {avatar}")
            instance.avatar = avatar
        
        try:
            updated_instance = super().update(instance, validated_data)
            logger.info(f"Profile updated successfully: {updated_instance}")
            return updated_instance
        except Exception as e:
            logger.exception(f"Error updating profile: {str(e)}")
            raise serializers.ValidationError(f"Error updating profile: {str(e)}")

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'movie', 'is_like']

class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'movie', 'content', 'created_at', 'updated_at', 'likes_count', 'is_liked_by_user']
        read_only_fields = ['id', 'created_at', 'updated_at', 'likes_count', 'is_liked_by_user']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

