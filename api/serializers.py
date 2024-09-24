from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Ban, UserProfile
from django.contrib.auth import get_user_model
from .models import Movie, UserProfile, Like, Comment,  Ban, BanAppeal, Notification
#Needed for cloudinary Avatar
from django.core.files.base import ContentFile
import base64
import logging


User = get_user_model()
logger = logging.getLogger('zaptalk_api.api')

class MovieSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Movie
        fields = fields = ['id', 'title', 'year', 'cast', 'genres', 'href', 'extract', 'thumbnail', 'thumbnail_width', 'thumbnail_height', 'likes_count', 'comments_count']

    def get_likes_count(self, obj):
        return obj.likes_count

    def get_comments_count(self, obj):
        return obj.comments_count

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='profile.avatar', required=False, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']

class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    comment_count = serializers.SerializerMethodField()
    total_likes_received = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)
    is_superuser = serializers.SerializerMethodField()
    is_banned = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user_id', 'id', 'username', 'email', 'avatar', 'bio', 'location', 'birth_date', 'website', 
                  'comment_count', 'total_likes_received', 'followers_count', 'following_count', 'is_following', 'is_superuser', 'is_banned']

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
            return request.user.profile in obj.followers.all()
        return False

    def get_is_superuser(self, obj):
        return obj.user.is_superuser

    def get_is_banned(self, obj):
        return obj.is_banned()
        
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
    user = serializers.SerializerMethodField()
    content_object = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    object_id = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)
    movie_title = serializers.SerializerMethodField()
    movie_details = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['id', 'user', 'content_type', 'object_id', 'content_object', 'created_at', 'movie_title', 'movie_details', 'type']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'avatar': obj.user.profile.avatar.url if hasattr(obj.user, 'profile') and obj.user.profile.avatar else None
        }
        
    # Gets content type
    def get_content_type(self, obj):
        if obj.content_type == Movie.get_default_like_content_type():
            return 'movie'
        elif obj.content_type == Comment.get_default_like_content_type():
            return 'comment'
        return None

    # Get likes on either movie or comment
    def get_content_object(self, obj):
        if obj.content_type == Movie.get_default_like_content_type():
            movie = obj.content_object
            return {
                'id': movie.id,
                'title': movie.title,
                'type': 'movie'
            }
        elif obj.content_type == Comment.get_default_like_content_type():
            comment = obj.content_object
            return {
                'id': comment.id,
                'content': comment.content[:50] + '...' if len(comment.content) > 50 else comment.content,
                'type': 'comment',
                'movie_id': comment.movie.id if comment.movie else None
            }
        return None
    
    #This is used for the feed page to get a like or a comment "Sandra Commented on x"
    def get_type(self, obj):
        if obj.content_type == Movie.get_default_like_content_type():
            return 'like'
        elif obj.content_type == Comment.get_default_like_content_type():
            return 'comment'
        return None

    def get_movie_title(self, obj):
        if obj.content_type == Movie.get_default_like_content_type():
            return obj.content_object.title
        elif obj.content_type == Comment.get_default_like_content_type():
            return obj.content_object.movie.title if obj.content_object.movie else None
        return None

    def get_movie_details(self, obj):
        if obj.content_type == Movie.get_default_like_content_type():
            movie = obj.content_object
        elif obj.content_type == Comment.get_default_like_content_type():
            movie = obj.content_object.movie
        else:
            return None

        if movie:
            return {
                'id': movie.id,
                'title': movie.title,
                'thumbnail': movie.thumbnail if hasattr(movie, 'thumbnail') else None
            }
        return None



class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    movie_details = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'movie', 'content', 'created_at', 'updated_at', 'likes_count', 'is_liked_by_user', 'movie_details']
        read_only_fields = ['id', 'created_at', 'updated_at', 'likes_count', 'is_liked_by_user']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_movie_details(self, obj):
        if obj.movie:
            return {
                'id': obj.movie.id,
                'title': obj.movie.title,
                'thumbnail': obj.movie.thumbnail if hasattr(obj.movie, 'thumbnail') else None
            }
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_representation = representation['user']
        if user_representation and 'profile' in user_representation:
            user_representation['avatar'] = user_representation['profile'].get('avatar')
        return representation

class BanSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    banned_by_username = serializers.CharField(source='banned_by.username', read_only=True)
    banned_by_id = serializers.IntegerField(source='banned_by.id', read_only=True)

    class Meta:
        model = Ban
        fields = ['id', 'username', 'user_id', 'user_username', 'banned_by_id', 'banned_by_username', 'reason', 'banned_at', 'expires_at', 'is_active']
        read_only_fields = ['id', 'user_id', 'user_username', 'banned_by_id', 'banned_by_username', 'banned_at']

    def create(self, validated_data):
        username = validated_data.pop('username')
        user = User.objects.filter(username=username).first()
        if not user:
            raise serializers.ValidationError(f"User with username '{username}' does not exist.")
        
        validated_data['user'] = user
        validated_data['banned_by'] = self.context['request'].user
        
        # Set the user's is_active to False
        user.is_active = False
        user.save()
        
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_active'] = instance.user.is_active
        return representation

class BanAppealSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    user_username = serializers.CharField(source='ban.user.username', read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)

    class Meta:
        model = BanAppeal
        fields = ['id', 'username', 'email', 'user_username', 'content', 'created_at', 'is_resolved']
        read_only_fields = ['id', 'user_username', 'created_at', 'is_resolved']

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        user = User.objects.filter(username=username).first()
        if not user:
            raise serializers.ValidationError(f"User with username '{username}' does not exist.")
        
        active_ban = Ban.objects.filter(user=user, is_active=True).first()
        if not active_ban:
            raise serializers.ValidationError(f"No active ban found for user '{username}'.")
        
        validated_data['ban'] = active_ban
        
        # Update user's email if it has changed
        if user.email != email:
            user.email = email
            user.save()
        
        return super().create(validated_data)
    
class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.profile.avatar', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'sender_username', 'sender_avatar', 'notification_type', 'is_read', 'created_at']