from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Movie, UserProfile, Like, Comment
from .serializers import MovieSerializer, UserSerializer, UserProfileSerializer, LikeSerializer, CommentSerializer
import random
import logging

logger = logging.getLogger(__name__)

#Pagination to only load 24 pages
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Movie.objects.filter(~Q(thumbnail__isnull=True) & ~Q(thumbnail__exact=''))

    @action(detail=False, methods=['get'])
    def random(self, request):
        queryset = self.get_queryset()
        count = queryset.count()
        if count == 0:
            return Response({"detail": "No movies with thumbnails available"}, status=status.HTTP_404_NOT_FOUND)
        random_index = random.randint(0, count - 1)
        random_movie = queryset[random_index]
        serializer = self.get_serializer(random_movie)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        try:
            user_to_follow = self.get_object()
            user = request.user.userprofile

            if user == user_to_follow:
                return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
            if user in user_to_follow.followers.all():
                user_to_follow.followers.remove(user)
                return Response({"detail": f"You have unfollowed {user_to_follow.user.username}."}, status=status.HTTP_200_OK)
            else:
                user_to_follow.followers.add(user)
                return Response({"detail": f"You are now following {user_to_follow.user.username}."}, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = user.followers.all()
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def following(self, request, pk=None):
        user = self.get_object()
        following = user.following.all()
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def likes(self, request, pk=None):
        user = self.get_object()
        likes = Like.objects.filter(user=user.user)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def toggle_like(self, request):
        try:
            user = request.user
            content_type = request.data.get('content_type')
            object_id = request.data.get('object_id')

            if not content_type or not object_id:
                return Response({"detail": "content_type and object_id are required"}, 
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                content_type = ContentType.objects.get(model=content_type)
                content_object = content_type.get_object_for_this_type(id=object_id)
            except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
                return Response({"detail": "Object not found"}, status=status.HTTP_404_NOT_FOUND)

            like, created = Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=object_id
            )

            if not created:
                like.delete()
                is_liked = False
            else:
                is_liked = True

            likes_count = Like.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).count()

            return Response({
                "is_liked": is_liked,
                "likes_count": likes_count
            })

        except Exception as e:
            logger.error(f"Error in toggle_like: {str(e)}")
            return Response({"detail": "An error occurred while processing your request"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CommentFilter(filters.FilterSet):
    movie = filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = Comment
        fields = ['movie']
        
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]  # Enable filtering
    filterset_class = CommentFilter  # Attach the filter class

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        # Assign the authenticated user to the comment
        serializer.save(user=self.request.user)