"""
Upload images to Cloudinary and update Hotel Killarney gallery
NOTE: For manual upload, use placeholder URLs temporarily
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, HotelPublicSettings
from django.conf import settings

# Check if Cloudinary is configured
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = bool(
        settings.CLOUDINARY_STORAGE and
        settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
    )
except:
    CLOUDINARY_AVAILABLE = False

# Image paths
images = [
    r'C:\Users\nlekk\HMB\HotelMateBackend\docs\images\room1.webp',
    r'C:\Users\nlekk\HMB\HotelMateBackend\docs\images\room2.webp',
    r'C:\Users\nlekk\HMB\HotelMateBackend\docs\images\room3.webp',
    r'C:\Users\nlekk\HMB\HotelMateBackend\docs\images\room4.webp',
]

def upload_gallery():
    # Get Hotel Killarney
    hotel = Hotel.objects.filter(slug='hotel-killarney').first()
    if not hotel:
        print("❌ Hotel Killarney not found")
        return
    
    # Get or create public settings
    settings_obj, created = HotelPublicSettings.objects.get_or_create(
        hotel=hotel
    )
    
    if not CLOUDINARY_AVAILABLE:
        print("⚠️ Cloudinary not configured. Using placeholder URLs for testing.\n")
        print("To upload real images to Cloudinary, add to settings:")
        print("  - CLOUDINARY_CLOUD_NAME")
        print("  - CLOUDINARY_API_KEY")
        print("  - CLOUDINARY_API_SECRET\n")
        
        # Use placeholder URLs
        gallery_urls = [
            'https://via.placeholder.com/800x600.webp?text=Room+1',
            'https://via.placeholder.com/800x600.webp?text=Room+2',
            'https://via.placeholder.com/800x600.webp?text=Room+3',
            'https://via.placeholder.com/800x600.webp?text=Room+4',
        ]
        
        settings_obj.gallery = gallery_urls
        settings_obj.save()
        
        print(f"✅ Gallery updated with {len(gallery_urls)} placeholder images")
        print("\n📋 Gallery URLs:")
        for i, url in enumerate(gallery_urls, 1):
            print(f"  {i}. {url}")
        return
    
    print(f"📸 Uploading images to Cloudinary for {hotel.name}...")
    
    gallery_urls = []
    
    for image_path in images:
        if not os.path.exists(image_path):
            print(f"⚠️  File not found: {image_path}")
            continue
        
        filename = os.path.basename(image_path)
        print(f"  Uploading {filename}...")
        
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                image_path,
                folder=f"hotels/{hotel.slug}/gallery",
                public_id=filename.replace('.webp', ''),
                resource_type='image'
            )
            
            url = result['secure_url']
            gallery_urls.append(url)
            print(f"  ✓ Uploaded: {url}")
            
        except Exception as e:
            print(f"  ❌ Error uploading {filename}: {e}")
    
    if gallery_urls:
        # Update gallery
        settings_obj.gallery = gallery_urls
        settings_obj.save()
        
        print(f"\n✅ Gallery updated with {len(gallery_urls)} images")
        print("\n📋 Gallery URLs:")
        for i, url in enumerate(gallery_urls, 1):
            print(f"  {i}. {url}")
    else:
        print("\n❌ No images were uploaded")

if __name__ == '__main__':
    upload_gallery()
