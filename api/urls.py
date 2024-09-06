from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, UserProfileViewSet, LikeViewSet, CommentViewSet, FollowViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'follows', FollowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/', include(router.urls)),
]