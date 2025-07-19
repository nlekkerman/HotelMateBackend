from django.db import models
from cloudinary.models import CloudinaryField


class Post(models.Model):
    author = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
    )
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
    )
    content = models.TextField(blank=True)
    image = CloudinaryField("image", blank=True, null=True)  # ✅ optional Cloudinary image
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author} @ {self.hotel.slug}"


class Like(models.Model):
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff', 'post')  # ✅ prevent double-liking

    def __str__(self):
        return f"{self.staff} liked {self.post.id}"


class Comment(models.Model):
    author = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    content = models.TextField()
    image = CloudinaryField("image", blank=True, null=True)  # ✅ comment with optional image
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on Post {self.post.id}"
