#!/usr/bin/env python
"""
Script to set up hotel default cancellation policy
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

try:
    django.setup()
    
    from hotel.models import Hotel, CancellationPolicy
    
    def setup_hotel_default_policy(hotel_slug, policy_code="FLEX24"):
        """Set up a default policy for a hotel"""
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
            print(f"✅ Found hotel: {hotel.name}")
            
            # Find or create default policy
            policy = CancellationPolicy.objects.filter(
                hotel=hotel, 
                code=policy_code
            ).first()
            
            if not policy:
                print(f"❌ No policy found with code '{policy_code}' for this hotel")
                print("Available policies:")
                for p in CancellationPolicy.objects.filter(hotel=hotel):
                    print(f"  - {p.code}: {p.name}")
                return
            
            # Set as hotel default
            hotel.default_cancellation_policy = policy
            hotel.save()
            
            print(f"✅ Set '{policy.name}' as default policy for {hotel.name}")
            print(f"   Policy ID: {policy.id}")
            print(f"   Template: {policy.template_type}")
            
        except Hotel.DoesNotExist:
            print(f"❌ Hotel '{hotel_slug}' not found")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def list_hotel_policies(hotel_slug):
        """List all policies for a hotel"""
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
            policies = CancellationPolicy.objects.filter(hotel=hotel)
            
            print(f"\n📋 Policies for {hotel.name}:")
            for policy in policies:
                is_default = "⭐ DEFAULT" if policy.id == hotel.default_cancellation_policy_id else ""
                print(f"  {policy.id}: {policy.code} - {policy.name} {is_default}")
                print(f"      Template: {policy.template_type}, Active: {policy.is_active}")
            
            if not policies.exists():
                print("  No policies found. Run seed command first.")
                
        except Hotel.DoesNotExist:
            print(f"❌ Hotel '{hotel_slug}' not found")
    
    if __name__ == "__main__":
        # Example usage
        hotel_slug = "hotel-killarney"  # Change this to your hotel slug
        
        print("=== Hotel Policy Manager ===")
        list_hotel_policies(hotel_slug)
        
        # Uncomment to set default policy:
        # setup_hotel_default_policy(hotel_slug, "FLEX24")
        
except Exception as e:
    print(f"❌ Setup error: {e}")
    print("Make sure you have the required dependencies installed.")