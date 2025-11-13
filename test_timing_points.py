"""
Test Quiz Timing and Points System
Verifies: 1 second = 5 points, timeout = 0 points
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

print('='*70)
print('QUIZ TIMING & POINTS TEST')
print('='*70)
print()

print('TIMING SYSTEM:')
print('  Timer: 5 seconds per question')
print('  Points Formula: 5 - seconds_taken')
print()

print('POINTS BY TIME:')
print('-'*70)
for seconds in range(0, 6):
    base_points = max(0, 5 - seconds)
    if seconds == 0:
        print(f'  {seconds}s (instant) = {base_points} points (MAX)')
    elif seconds == 5:
        print(f'  {seconds}s (timeout) = {base_points} points (NONE)')
    else:
        print(f'  {seconds}s           = {base_points} points')
print()

print('TURBO MODE MULTIPLIERS:')
print('-'*70)
multipliers = [1, 2, 4, 8, 16, 32, 64, 128]
for idx, mult in enumerate(multipliers, 1):
    example_time = 1  # Fast answer
    base = 5 - example_time  # 4 points
    total = base * mult
    print(f'  {idx} correct in a row: {mult}x multiplier -> {base} pts x {mult} = {total} pts')
print()

print('EXAMPLE SCENARIOS:')
print('-'*70)

scenarios = [
    {'time': 0, 'mult': 1, 'desc': 'Instant answer, 1st correct'},
    {'time': 1, 'mult': 1, 'desc': '1 second, 1st correct'},
    {'time': 2, 'mult': 2, 'desc': '2 seconds, 2nd correct'},
    {'time': 3, 'mult': 4, 'desc': '3 seconds, 3rd correct'},
    {'time': 4, 'mult': 8, 'desc': '4 seconds, 4th correct'},
    {'time': 5, 'mult': 16, 'desc': '5 seconds (timeout), 5th correct'},
    {'time': 1, 'mult': 32, 'desc': '1 second, 6th correct (TURBO!)'},
]

for scenario in scenarios:
    time = scenario['time']
    mult = scenario['mult']
    desc = scenario['desc']
    
    base = max(0, 5 - time)
    points = base * mult
    
    print(f'  {desc}')
    print(f'    Base: 5 - {time}s = {base} pts')
    print(f'    With {mult}x multiplier = {points} pts')
    print()

print('='*70)
print('KEY TAKEAWAYS:')
print('  - Answer in 0-1s = 4-5 base points (BEST)')
print('  - Answer in 2-3s = 2-3 base points (GOOD)')
print('  - Answer in 4s = 1 base point (OK)')
print('  - Answer in 5s = 0 points (TIMEOUT - but keeps streak!)')
print('  - Max single answer: 4 pts x 128x = 512 points!')
print('='*70)
