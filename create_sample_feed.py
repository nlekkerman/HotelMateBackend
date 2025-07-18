#!/usr/bin/env python3
import os
import django

# ————————————————————————————————
# 1) Configure Django
#    Replace 'HotelMateBackend.settings' with your actual settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()
# ————————————————————————————————

from staff.models import Staff
from hotel.models import Hotel
from home.models import Post, Comment

# ————————————————————————————————
# 2) Parameters: adjust as needed
HOTEL_SLUG        = 'hotel-killarney'
NUM_POSTS         = 5
COMMENTS_PER_POST = 2
# ————————————————————————————————

def main():
    try:
        hotel = Hotel.objects.get(slug=HOTEL_SLUG)
    except Hotel.DoesNotExist:
        print(f"❌ Hotel with slug '{HOTEL_SLUG}' not found.")
        return

    staff_qs = Staff.objects.filter(hotel=hotel, is_active=True)
    staff_list = list(staff_qs[:NUM_POSTS or None])
    if not staff_list:
        print(f"❌ No active staff found for hotel '{HOTEL_SLUG}'.")
        return

    print(f"ℹ️  Creating {NUM_POSTS} posts for hotel '{HOTEL_SLUG}' using {len(staff_list)} staff members.")

    for i in range(NUM_POSTS):
        author = staff_list[i % len(staff_list)]
        post = Post.objects.create(
            author=author,
            hotel=hotel,
            content=f"Sample post #{i+1} by {author.first_name} {author.last_name}",
        )
        print(f"  ✓ Created Post id={post.id}")

        for j in range(COMMENTS_PER_POST):
            commenter = staff_list[(i + j + 1) % len(staff_list)]
            comment = Comment.objects.create(
                author=commenter,
                post=post,
                content=f"Comment #{j+1} on post #{i+1} by {commenter.first_name}",
            )
            print(f"    – Created Comment id={comment.id}")

    print("🎉 Done creating sample posts and comments.")

if __name__ == '__main__':
    main()
