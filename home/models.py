from django.db import models


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
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
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
        unique_together = ('staff', 'post')


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
    created_at = models.DateTimeField(auto_now_add=True)
