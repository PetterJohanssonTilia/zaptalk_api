from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Movie, UserProfile, Like, Comment, Follow
from .serializers import MovieSerializer, UserSerializer, UserProfileSerializer, LikeSerializer, CommentSerializer, FollowSerializer
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
    permission_classes = [IsAuthenticated]

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