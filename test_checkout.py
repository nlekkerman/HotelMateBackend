#!/usr/bin/env python3
"""
Quick test script to confirm checkout endpoint behavior
Tests both room IDs vs room numbers
"""
import requests
import json

# Configuration
BASE_URL = "https://hotel-porter-d25ad83b12cf.herokuapp.com"
HOTEL_SLUG = "hotel-killarney"

def test_checkout_with_ids():
    """Test checkout with room database IDs"""
    url = f"{BASE_URL}/api/staff/hotel/{HOTEL_SLUG}/rooms/checkout/"
    
    # Test with database IDs (numbers)
    payload = {
        "room_ids": [1, 2, 3]  # Database IDs
    }
    
    print(f"Testing checkout with room IDs: {payload}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("-" * 50)

def test_checkout_with_room_numbers():
    """Test checkout with room numbers (should fail)"""
    url = f"{BASE_URL}/api/staff/hotel/{HOTEL_SLUG}/rooms/checkout/"
    
    # Test with room numbers (strings)
    payload = {
        "room_ids": ["301", "302", "303"]  # Room numbers
    }
    
    print(f"Testing checkout with room numbers: {payload}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("-" * 50)

def test_empty_room_ids():
    """Test with empty room_ids (should fail with your original error)"""
    url = f"{BASE_URL}/api/staff/hotel/{HOTEL_SLUG}/rooms/checkout/"
    
    # Test with empty list
    payload = {
        "room_ids": []
    }
    
    print(f"Testing checkout with empty room_ids: {payload}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("-" * 50)

def test_missing_room_ids():
    """Test without room_ids field (should fail with your original error)"""
    url = f"{BASE_URL}/api/staff/hotel/{HOTEL_SLUG}/rooms/checkout/"
    
    # Test with missing room_ids
    payload = {}
    
    print(f"Testing checkout with missing room_ids: {payload}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("-" * 50)

if __name__ == "__main__":
    print("Testing checkout endpoint behavior...\n")
    
    # Test different scenarios
    test_missing_room_ids()      # Should reproduce your original error
    test_empty_room_ids()        # Should reproduce your original error
    test_checkout_with_room_numbers()  # Should fail - wrong data type
    test_checkout_with_ids()     # Should work (if rooms exist)
    
    print("Done!")