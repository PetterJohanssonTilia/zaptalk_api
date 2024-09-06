from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Movie, UserProfile, Like, Comment, Follow

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = fields = ['id', 'title', 'year', 'cast', 'genres', 'href', 'extract', 'thumbnail', 'thumbnail_width', 'thumbnail_height']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user']

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

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    followed = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed']