from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import Movie, UserProfile, Like, Comment, Follow
from .serializers import MovieSerializer, UserSerializer, UserProfileSerializer, LikeSerializer, CommentSerializer, FollowSerializer
import random

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def random(self, request):
        movies = list(Movie.objects.all())
        if movies:
            random_movie = random.choice(movies)
            serializer = self.get_serializer(random_movie)
            return Response(serializer.data)
        return Response({"detail": "No movies available"}, status=status.HTTP_404_NOT_FOUND)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def toggle_like(self, request):
        user = request.user
        movie_id = request.data.get('movie_id')
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = Like.objects.get_or_create(user=user, movie=movie)
        if not created:
            like.is_like = not like.is_like
            like.save()
        
        serializer = self.get_serializer(like)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def toggle_follow(self, request):
        follower = request.user
        followed_id = request.data.get('followed_id')
        try:
            followed = User.objects.get(id=followed_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        follow, created = Follow.objects.get_or_create(follower=follower, followed=followed)
        if not created:
            follow.delete()
            return Response({"detail": "Unfollowed successfully"}, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(follow)
        return Response(serializer.data)