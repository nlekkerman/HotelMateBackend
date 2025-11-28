#!/usr/bin/env python
"""
Test script to check the enhanced room type API response
"""
import requests
import json

def test_room_types():
    try:
        # Get the hotel page data
        response = requests.get('http://127.0.0.1:8000/api/public/hotel/hotel-killarney/page/')
        response.raise_for_status()
        
        data = response.json()
        
        # Find the rooms section
        rooms_section = next((s for s in data['sections'] if s['section_type'] == 'rooms'), None)
        
        if not rooms_section:
            print("No rooms section found")
            return
        
        room_types = rooms_section['rooms_data']['room_types']
        
        print(f"=== ENHANCED ROOM TYPES API RESPONSE ===")
        print(f"Total room variants: {len(room_types)}")
        print()
        
        for i, rt in enumerate(room_types):
            print(f"{i+1}. {rt['room_type_name']}")
            print(f"   Rate Plan: {rt['rate_plan_name']} ({rt['rate_plan_code']})")
            print(f"   Price: {rt['price_display']} (Current: {rt['current_price']}, Original: {rt['original_price']})")
            print(f"   Discount: {rt['discount_percent']}% {'✅' if rt['has_discount'] else '❌'}")
            print(f"   Refundable: {'✅' if rt['is_refundable'] else '❌'}")
            print(f"   Booking URL: {rt['booking_cta_url']}")
            print()
            
            if i >= 8:  # Limit output
                break
        
        print(f"... and {len(room_types) - 9} more variants" if len(room_types) > 9 else "")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_room_types()