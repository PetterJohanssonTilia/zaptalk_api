from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

#Creates a default content type for the likes that changes inside of comments/movies
def get_default_content_type():
    return ContentType.objects.get_for_model(Movie).id

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
    likes = GenericRelation(Like, related_query_name='movie')
    
    @staticmethod
    def get_default_like_content_type():
        return ContentType.objects.get_for_model(Movie)

    @property
    def likes_count(self):
        return self.likes.count()

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = CloudinaryField('image', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')

    def __str__(self):
        return self.user.username
    
    def get_comment_count(self):
        return self.user.comment_set.count()

    def get_total_likes_received(self):
        comments = self.user.comment_set.all()
        return sum(comment.likes.count() for comment in comments)
    
    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.following.count()
    
    def is_following(self, user_to_check):
        return self.following.filter(user=user_to_check).exists()

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = GenericRelation(Like, related_query_name='comment')


    @staticmethod
    def get_default_like_content_type():
        return ContentType.objects.get_for_model(Comment)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.movie.title}'


class Ban(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ban')
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bans_issued')
    reason = models.TextField()
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Ban for {self.user.username}"

class BanAppeal(models.Model):
    ban = models.ForeignKey(Ban, on_delete=models.CASCADE, related_name='appeals')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(null=True, default=None)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ban_appeals_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Appeal for {self.ban.user.username}'s ban"