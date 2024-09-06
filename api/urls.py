from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from .views import MovieViewSet, UserProfileViewSet, LikeViewSet, CommentViewSet, FollowViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'follows', FollowViewSet)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response({
        'movies': reverse('movie-list', request=request, format=format),
        'profiles': reverse('userprofile-list', request=request, format=format),
        'likes': reverse('like-list', request=request, format=format),
        'comments': reverse('comment-list', request=request, format=format),
        'follows': reverse('follow-list', request=request, format=format),
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
]