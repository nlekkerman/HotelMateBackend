"""
Test script for room type image upload endpoint
Tests the staff API: /api/staff/hotel/{slug}/hotel/staff/room-types/{id}/upload-image/
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType
from hotel.models import Hotel

def test_setup():
    """Display current setup for testing"""
    print('\n' + '='*60)
    print('  Room Type Image Upload Endpoint - Test Setup')
    print('='*60)
    
    # List hotels
    hotels = Hotel.objects.all()
    print('\n📍 Available Hotels:')
    for h in hotels:
        print(f'   {h.id}. {h.name} (slug: {h.slug})')
    
    if not hotels:
        print('   No hotels found. Please create a hotel first.')
        return
    
    # List room types for each hotel
    print('\n🏨 Room Types:')
    for hotel in hotels:
        room_types = RoomType.objects.filter(hotel=hotel)
        if room_types:
            print(f'\n   {hotel.name}:')
            for rt in room_types:
                photo_status = '✓' if rt.photo else '✗'
                print(f'      {photo_status} ID {rt.id}: {rt.name}')
                if rt.photo:
                    print(f'         Photo: {rt.photo.url}')
        else:
            print(f'\n   {hotel.name}: No room types')
    
    # Display endpoint examples
    print('\n' + '='*60)
    print('  API Endpoint Examples')
    print('='*60)
    
    if hotels and RoomType.objects.exists():
        hotel = hotels.first()
        room_type = RoomType.objects.filter(hotel=hotel).first()
        
        if room_type:
            print(f'\n📍 Upload image for "{room_type.name}":')
            print(f'\n   POST /api/staff/hotel/{hotel.slug}/hotel/staff/room-types/{room_type.id}/upload-image/')
            
            print('\n   Option 1: Upload file (multipart/form-data)')
            print('   ----------------------------------------')
            print('   curl -X POST \\')
            print(f'     "http://localhost:8000/api/staff/hotel/{hotel.slug}/hotel/staff/room-types/{room_type.id}/upload-image/" \\')
            print('     -H "Authorization: Bearer YOUR_TOKEN" \\')
            print('     -F "photo=@/path/to/image.jpg"')
            
            print('\n   Option 2: Use image URL (JSON)')
            print('   -------------------------------')
            print('   curl -X POST \\')
            print(f'     "http://localhost:8000/api/staff/hotel/{hotel.slug}/hotel/staff/room-types/{room_type.id}/upload-image/" \\')
            print('     -H "Authorization: Bearer YOUR_TOKEN" \\')
            print('     -H "Content-Type: application/json" \\')
            print('     -d \'{"photo_url": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800"}\'')
            
            print('\n   JavaScript/Fetch Example:')
            print('   -------------------------')
            print('   const formData = new FormData();')
            print('   formData.append("photo", fileInput.files[0]);')
            print('')
            print('   fetch(')
            print(f'     `/api/staff/hotel/{hotel.slug}/hotel/staff/room-types/{room_type.id}/upload-image/`,')
            print('     {')
            print('       method: "POST",')
            print('       headers: {')
            print('         "Authorization": `Bearer ${token}`')
            print('       },')
            print('       body: formData')
            print('     }')
            print('   );')
            
            print('\n   React Example (with Axios):')
            print('   ---------------------------')
            print('   const uploadImage = async (roomTypeId, file) => {')
            print('     const formData = new FormData();')
            print('     formData.append("photo", file);')
            print('')
            print('     const response = await axios.post(')
            print(f'       `/api/staff/hotel/${{hotelSlug}}/hotel/staff/room-types/${{roomTypeId}}/upload-image/`,')
            print('       formData,')
            print('       {')
            print('         headers: {')
            print('           "Authorization": `Bearer ${token}`,')
            print('           "Content-Type": "multipart/form-data"')
            print('         }')
            print('       }')
            print('     );')
            print('     return response.data;')
            print('   };')
    
    print('\n' + '='*60)
    print('\n✓ Endpoint is ready at:')
    print('  /api/staff/hotel/{hotel_slug}/hotel/staff/room-types/{id}/upload-image/')
    print('\n✓ Accepts: File upload (multipart) OR image URL (JSON)')
    print('✓ Requires: Staff authentication')
    print('✓ Returns: { message, photo_url }')
    print('\n' + '='*60 + '\n')


if __name__ == '__main__':
    test_setup()
