from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Movie, UserProfile, Like, Comment

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
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'avatar', 'bio', 'location', 'birth_date', 'website', 
                  'comment_count', 'total_likes_received', 'follower_count', 'following_count', 'is_following']

    def get_comment_count(self, obj):
        return obj.get_comment_count()

    def get_total_likes_received(self, obj):
        return obj.get_total_likes_received()

    def get_follower_count(self, obj):
        return obj.get_follower_count()

    def get_following_count(self, obj):
        return obj.get_following_count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.userprofile in obj.followers.all()
        return False


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'movie', 'is_like']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'movie', 'content', 'created_at']

