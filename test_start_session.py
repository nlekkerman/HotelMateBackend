"""
Quick test for start_session endpoint
"""
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from entertainment.views import QuizGameViewSet

print("=" * 70)
print("TEST: Start Session Endpoint")
print("=" * 70)

factory = APIRequestFactory()

# Create a POST request
data = {
    'player_name': 'TestPlayer',
    'session_token': str(uuid.uuid4()),
    'is_tournament_mode': False
}

request = factory.post(
    '/api/entertainment/quiz/game/start_session/',
    data,
    format='json'
)

# Create the view and call it
view = QuizGameViewSet.as_view({'post': 'start_session'})

try:
    response = view(request)
    response.render()
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ SUCCESS!")
        print(f"\nResponse Keys: {list(response.data.keys())}")
        
        if 'session' in response.data:
            print(f"Session ID: {response.data['session']['id']}")
            print(f"Player: {response.data['session']['player_name']}")
        
        if 'categories' in response.data:
            print(f"Categories: {len(response.data['categories'])}")
            for cat in response.data['categories']:
                print(f"  - {cat['name']} ({cat['slug']})")
        
        if 'game_rules' in response.data:
            print(f"Game Rules: ✓")
    else:
        print("❌ FAILED!")
        print(f"Error: {response.data}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
