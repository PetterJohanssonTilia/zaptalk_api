from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from .views import MovieViewSet, UserProfileViewSet, LikeViewSet, CommentViewSet, BanViewSet, BanAppealViewSet, get_genres, NotificationViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'likes', LikeViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'bans', BanViewSet)
router.register(r'ban-appeals', BanAppealViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('genres/', get_genres, name='get_genres'),  # This is only a function view and why it's not in the router.register
]