from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.user.username} likes {self.content_object}"

class Movie(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField(default=0)
    cast = models.JSONField(default=list)
    genres = models.JSONField(default=list)
    href = models.CharField(max_length=200, null=True, blank=True)
    extract = models.TextField(default='')
    thumbnail = models.URLField(max_length=500, default='https://example.com/placeholder.jpg')
    thumbnail_width = models.IntegerField(null=True, blank=True)
    thumbnail_height = models.IntegerField(null=True, blank=True)
    likes = GenericRelation('Like')
    
    @property
    def likes_count(self):
        return self.likes.count()

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.user.username

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = GenericRelation('Like')

    def __str__(self):
        return f'Comment by {self.user.username} on {self.movie.title}'

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"