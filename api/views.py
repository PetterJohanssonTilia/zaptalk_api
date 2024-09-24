from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Q, Count, Case, When, IntegerField, Subquery
from django_filters import rest_framework as filters
from .models import Movie, UserProfile, Like, Comment, Ban, BanAppeal
from .serializers import MovieSerializer, UserSerializer, UserProfileSerializer, LikeSerializer, CommentSerializer, BanSerializer, BanAppealSerializer, NotificationSerializer

import random
import logging

logger = logging.getLogger('zaptalk_api.api')

#Get all the genres
@api_view(['GET'])
def get_genres(request):
    genres = Movie.objects.values_list('genres', flat=True)
    unique_genres = set()
    for genre_list in genres:
        if genre_list:  # Check if the list is not None
            unique_genres.update(genre_list)
    return Response(sorted(list(unique_genres)))

#Pagination to only load 24 pages
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

class MovieFilter(filters.FilterSet):
    genres = filters.CharFilter(method='filter_genres')
    search = filters.CharFilter(method='search_movies')
    sort = filters.CharFilter(method='sort_movies')
    followed_likes = filters.BooleanFilter(method='filter_followed_likes')

    class Meta:
        model = Movie
        fields = ['genres', 'search', 'sort', 'followed_likes']

    def filter_genres(self, queryset, name, value):
        genres = [genre.strip().lower() for genre in value.split(',') if genre.strip()]
        logger.info(f"Filtering for genres: {genres}")
        if genres:
            genre_q = Q()
            for genre in genres:
                genre_q |= Q(genres__icontains=genre)
            
            filtered = queryset.filter(genre_q).distinct()
            logger.info(f"SQL Query: {filtered.query}")
            logger.info(f"Filtered queryset count: {filtered.count()}")
            return filtered
        return queryset

    def search_movies(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(extract__icontains=value))

    def sort_movies(self, queryset, name, value):
        if value == 'most_liked':
            return queryset.annotate(like_count=Count('likes')).order_by('-like_count')
        elif value == 'most_commented':
            return queryset.annotate(comment_count=Count('comments')).order_by('-comment_count')
        elif value == 'genres':
            selected_genres = self.request.query_params.get('genres', '').split(',')
            return queryset.annotate(
                matched_genres_count=Count(
                    Case(
                        When(genres__name__in=selected_genres, then=1),
                        output_field=IntegerField()
                    )
                )
            ).order_by('-matched_genres_count', 'title')
        return queryset

    def filter_followed_likes(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            followed_users = self.request.user.profile.following.values_list('user', flat=True)
            return queryset.filter(likes__user__in=followed_users).distinct()
        return queryset

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MovieFilter

    def get_queryset(self):
        base_queryset = Movie.objects.filter(~Q(thumbnail__isnull=True) & ~Q(thumbnail__exact=''))
        logger.info(f"Base queryset count: {base_queryset.count()}")
        logger.info(f"Request parameters: {self.request.query_params}")

        filtered_queryset = self.filterset_class(self.request.GET, queryset=base_queryset, request=self.request).qs
        
        followed_likes = self.request.query_params.get('followed_likes', '').lower() == 'true'
        if followed_likes and self.request.user.is_authenticated:
            followed_users = self.request.user.profile.following.values_list('user', flat=True)
            liked_movies = Like.objects.filter(
                user__in=followed_users, 
                content_type=ContentType.objects.get_for_model(Movie)
            ).values_list('object_id', flat=True)
            
            filtered_queryset = filtered_queryset.filter(id__in=Subquery(liked_movies)).distinct()

        logger.info(f"Filtered queryset count: {filtered_queryset.count()}")
        
        sample_movies = filtered_queryset[:5]
        logger.info("Sample movies from filtered queryset:")
        for movie in sample_movies:
            logger.info(f"- {movie.title} (Genres: {movie.genres})")

        return filtered_queryset
    
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        logger.info(f"Filtered queryset count: {queryset.count()}")
        logger.info(f"Request params: {request.query_params}")
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info(f"Serialized data length: {len(serializer.data)}")
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Serialized data length: {len(serializer.data)}")
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)
        
        if lookup_value.isdigit():
            # If the lookup value is a number, try to fetch by ID
            obj = get_object_or_404(queryset, pk=lookup_value)
        else:
            # If it's not a number, try to fetch by username
            obj = get_object_or_404(queryset, user__username=lookup_value)
        
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=False, methods=['get', 'put', 'delete'], permission_classes=[IsAuthenticated])
    def me(self, request):
        profile = request.user.profile
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method == 'PUT':
            logger.info(f"Received PUT request for user {request.user.username}")
            logger.info(f"Request data: {request.data}")
            
            try:
                serializer = self.get_serializer(profile, data=request.data, partial=True)
                if serializer.is_valid():
                    logger.info("Serializer is valid")
                    updated_profile = serializer.save()
                    logger.info(f"Profile updated successfully: {updated_profile}")
                    return Response(serializer.data)
                else:
                    logger.error(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.exception(f"Error updating profile: {str(e)}")
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == 'DELETE':
            user = request.user
            user.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def feed(self, request):
        user = request.user
        following = user.profile.following.all()
        following_users = [profile.user for profile in following]
        
        comments = Comment.objects.filter(user__in=following_users).order_by('-created_at')
        likes = Like.objects.filter(user__in=following_users).order_by('-created_at')
        
        comments_serializer = CommentSerializer(comments, many=True, context={'request': request})
        likes_serializer = LikeSerializer(likes, many=True)
        
        comment_items = [dict(item, **{'type': 'comment'}) for item in comments_serializer.data]
        like_items = [dict(item, **{'type': 'like'}) for item in likes_serializer.data]
        
        feed_items = sorted(
            comment_items + like_items,
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        return Response(feed_items)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        try:
            user_to_follow = self.get_object()
            user = request.user.profile

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

    # Following, shown on other users for example
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def following(self, request, pk=None):
        user = self.get_object()
        following = user.following.all()
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)

    # List of users you follow, shown on your profile page
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def following_list(self, request, pk=None):
        try:
            if pk == 'me':
                user_profile = request.user.profile
            else:
                user_profile = self.get_object()
            
            following = user_profile.following.all()
            following_data = [
                {
                    'user_id': profile.user.id,
                    'profile_id': profile.id,
                    'username': profile.user.username,
                    'avatar': profile.avatar.url if profile.avatar else None
                }
                for profile in following
            ]
            return Response(following_data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def likes(self, request, pk=None):
        user = self.get_object()
        likes = Like.objects.filter(user=user.user)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def is_banned(self, request, pk=None):
        profile = self.get_object()
        is_banned = Ban.objects.filter(user=profile.user, is_active=True).exists()
        return Response({'is_banned': is_banned})

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            likes = Like.objects.filter(
                content_type__in=[
                    Movie.get_default_like_content_type(),
                    Comment.get_default_like_content_type()
                ]
            ).order_by('-created_at')
            serializer = self.get_serializer(likes, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in LikeViewSet list: {str(e)}")
            return Response({"detail": "An error occurred while fetching likes"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def toggle_like(self, request):
        try:
            user = request.user
            content_type_str = request.data.get('content_type')
            object_id = request.data.get('object_id')

            if not content_type_str or not object_id:
                return Response({"detail": "content_type and object_id are required"}, 
                                status=status.HTTP_400_BAD_REQUEST)

            if content_type_str == 'movie':
                content_type = Movie.get_default_like_content_type()
            elif content_type_str == 'comment':
                content_type = Comment.get_default_like_content_type()
            else:
                return Response({"detail": "Invalid content_type"}, status=status.HTTP_400_BAD_REQUEST)

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

# Bans
class BanViewSet(viewsets.ModelViewSet):
    queryset = Ban.objects.all()
    serializer_class = BanSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def ban_user(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ban = serializer.save()
            return Response({
                "message": f"User {ban.user.username} banned successfully",
                "ban": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active_bans(self, request):
        active_bans = Ban.objects.filter(is_active=True)
        serializer = self.get_serializer(active_bans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def unban_user(self, request):
        username = request.data.get('username')
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"message": f"User {username} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        active_bans = Ban.objects.filter(user=user, is_active=True)
        if not active_bans.exists():
            return Response({"message": f"No active ban found for user {username}"}, status=status.HTTP_404_NOT_FOUND)
        
        for ban in active_bans:
            ban.is_active = False
            ban.save()
        
        user.is_active = True
        user.save()
        
        # Resolve all active ban appeals for this user
        active_appeals = BanAppeal.objects.filter(ban__user=user, is_resolved=False)
        for appeal in active_appeals:
            appeal.is_resolved = True
            appeal.save()
        
        return Response({"message": f"User {username} has been unbanned successfully and all ban appeals have been resolved"}, status=status.HTTP_200_OK)

class BanAppealViewSet(viewsets.ModelViewSet):
    queryset = BanAppeal.objects.filter(is_resolved=False)
    serializer_class = BanAppealSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "message": "Ban appeal submitted successfully",
                "appeal": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)