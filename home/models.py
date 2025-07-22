# src/home/models.py

from django.db import models
from cloudinary.models import CloudinaryField

class Post(models.Model):
    author     = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
    )
    hotel      = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
    )
    content    = models.TextField(blank=True)
    image      = CloudinaryField("image", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author} @ {self.hotel.slug}"


class Like(models.Model):
    staff      = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
    )
    post       = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff', 'post')

    def __str__(self):
        return f"{self.staff} liked post #{self.post.id}"


class Comment(models.Model):
    author     = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    post       = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    content    = models.TextField()
    image      = CloudinaryField("image", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment #{self.id} by {self.author}"


class CommentReply(models.Model):
    author     = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='replies',
    )
    comment    = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='replies',
    )
    content    = models.TextField()
    image      = CloudinaryField("image", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply #{self.id} to comment #{self.comment.id}"
