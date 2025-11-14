"""
Test Category Loading Bug - Math at Position 4
Simulates the frontend behavior where first category works fine,
but second category starts to get crazy/buggy behavior
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import override_settings
from rest_framework.test import APIClient
from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizAnswer,
    QuizSession, QuizPlayerProgress
)
import uuid


def setup_categories_with_math_at_4():
    """Setup 5 categories with math at position 4"""
    print("=" * 80)
    print("SETTING UP CATEGORIES - Math at Position 4")
    print("=" * 80)
    
    # Get or create the quiz
    quiz, _ = Quiz.objects.get_or_create(
        slug='guessticulator',
        defaults={
            'title': 'Guessticulator The Quizculator',
            'description': 'The ultimate quiz game',
            'questions_per_category': 10,
            'time_per_question_seconds': 5,
            'turbo_mode_threshold': 5,
            'turbo_multiplier': 2.0,
            'is_active': True
        }
    )
    
    # Define categories in order (math at position 4)
    categories_config = [
        {
            'slug': 'classic-trivia',
            'name': 'Classic Trivia',
            'description': 'General knowledge',
            'order': 1,
            'is_math_category': False
        },
        {
            'slug': 'odd-one-out',
            'name': 'Odd One Out',
            'description': 'Find the odd one',
            'order': 2,
            'is_math_category': False
        },
        {
            'slug': 'fill-the-blank',
            'name': 'Fill the Blank',
            'description': 'Complete the phrase',
            'order': 3,
            'is_math_category': False
        },
        {
            'slug': 'dynamic-math',
            'name': 'Dynamic Math',
            'description': 'Math challenges',
            'order': 4,  # MATH AT POSITION 4
            'is_math_category': True
        },
        {
            'slug': 'knowledge-trap',
            'name': 'Knowledge Trap',
            'description': 'Tricky questions',
            'order': 5,
            'is_math_category': False
        }
    ]
    
    categories = []
    for config in categories_config:
        category, created = QuizCategory.objects.update_or_create(
            slug=config['slug'],
            defaults={
                'name': config['name'],
                'description': config['description'],
                'order': config['order'],
                'is_math_category': config['is_math_category'],
                'is_active': True
            }
        )
        categories.append(category)
        
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} Category {config['order']}: {config['name']} "
              f"(Math: {config['is_math_category']})")
        
        # Create questions for non-math categories
        if not config['is_math_category']:
            existing_count = QuizQuestion.objects.filter(category=category).count()
            if existing_count < 15:
                needed = 15 - existing_count
                print(f"   Creating {needed} questions...")
                for i in range(needed):
                    question = QuizQuestion.objects.create(
                        category=category,
                        text=f'{config["name"]} Question {existing_count + i + 1}?',
                        is_active=True
                    )
                    # Create answers
                    QuizAnswer.objects.create(
                        question=question,
                        text=f'Correct Answer {i+1}',
                        is_correct=True,
                        order=0
                    )
                    for j in range(3):
                        QuizAnswer.objects.create(
                            question=question,
                            text=f'Wrong Answer {j+1}',
                            is_correct=False,
                            order=j+1
                        )
            else:
                print(f"   Already has {existing_count} questions")
    
    print(f"\n✅ Setup complete - {len(categories)} categories configured")
    return categories


def test_category_by_category_loading():
    """Test loading categories one by one (simulating frontend behavior)"""
    print("\n" + "=" * 80)
    print("TEST: Category-by-Category Loading (Frontend Simulation)")
    print("=" * 80)
    
    client = APIClient()
    client.credentials(HTTP_HOST='localhost:8000')
    session_token = str(uuid.uuid4())
    
    # Step 1: Start Session
    print("\n📍 Step 1: Start Session")
    print("-" * 80)
    response = client.post(
        '/api/entertainment/quiz/game/start_session/',
        data={
            'player_name': 'BugTestPlayer',
            'session_token': session_token,
            'is_tournament_mode': False
        },
        format='json'
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to start session: {response.status_code}")
        try:
            print(json.dumps(response.data, indent=2))
        except AttributeError:
            print(f"Response content: {response.content}")
        return
    
    session_id = response.data['session']['id']
    all_categories = response.data['categories']
    
    print(f"✅ Session started: ID={session_id}")
    print(f"📋 All Categories ({len(all_categories)}):")
    for cat in all_categories:
        math_indicator = "🔢" if cat.get('is_math_category') else "📝"
        print(f"   {math_indicator} {cat['order']}. {cat['name']} "
              f"(slug: {cat['slug']}, math: {cat.get('is_math_category', False)})")
    
    # Step 2: Load each category and submit answers
    print("\n📍 Step 2: Loading Categories One by One")
    print("-" * 80)
    
    for idx, category in enumerate(all_categories, 1):
        print(f"\n{'='*60}")
        print(f"LOADING CATEGORY {idx}/{len(all_categories)}: {category['name']}")
        print(f"{'='*60}")
        print(f"Category Details:")
        print(f"  - Slug: {category['slug']}")
        print(f"  - Order: {category['order']}")
        print(f"  - Is Math: {category.get('is_math_category', False)}")
        
        # Fetch questions for this category
        print("\n🔍 Fetching questions...")
        fetch_response = client.get(
            '/api/entertainment/quiz/game/fetch_category_questions/',
            {
                'session_id': session_id,
                'category_slug': category['slug']
            }
        )
        
        if fetch_response.status_code != 200:
            print(f"❌ Failed to fetch questions: {fetch_response.status_code}")
            print(json.dumps(fetch_response.data, indent=2))
            continue
        
        questions = fetch_response.data.get('questions', [])
        category_info = fetch_response.data.get('category', {})
        
        print(f"✅ Got {len(questions)} questions")
        print(f"\nCategory Info from Response:")
        print(f"  - ID: {category_info.get('id')}")
        print(f"  - Name: {category_info.get('name')}")
        print(f"  - Slug: {category_info.get('slug')}")
        print(f"  - Order: {category_info.get('order')}")
        print(f"  - Is Math: {category_info.get('is_math_category')}")
        
        # Check for inconsistencies (THE BUG)
        if category_info.get('slug') != category['slug']:
            print(f"\n⚠️ CATEGORY MISMATCH DETECTED!")
            print(f"   Expected: {category['slug']}")
            print(f"   Got: {category_info.get('slug')}")
        
        if category_info.get('order') != category['order']:
            print(f"\n⚠️ ORDER MISMATCH DETECTED!")
            print(f"   Expected: {category['order']}")
            print(f"   Got: {category_info.get('order')}")
        
        # Display first 3 questions
        print(f"\n📄 Sample Questions:")
        for i, q in enumerate(questions[:3], 1):
            is_math = 'question_data' in q
            q_type = "🔢 MATH" if is_math else "📝 REGULAR"
            print(f"   {q_type} Q{i}: {q['text'][:60]}...")
            if is_math:
                print(f"      Math Data: {q.get('question_data', {})}")
            print(f"      Category Slug: {q.get('category_slug', 'N/A')}")
            print(f"      Category Name: {q.get('category_name', 'N/A')}")
            print(f"      Category Order: {q.get('category_order', 'N/A')}")
            
            # Check if question category matches current category
            if q.get('category_slug') != category['slug']:
                print(f"      ⚠️ WRONG CATEGORY! Expected {category['slug']}, "
                      f"got {q.get('category_slug')}")
        
        # Submit answers for all questions
        print(f"\n📤 Submitting answers...")
        submitted = 0
        errors = 0
        
        for q_num, question in enumerate(questions, 1):
            # Get correct answer
            if 'question_data' in question:
                # Math question
                correct_answer = str(question['question_data']['correct_answer'])
                correct_answer_id = None
            else:
                # Regular question
                correct_answers = [a for a in question.get('answers', []) 
                                 if 'Correct' in a.get('text', '')]
                if correct_answers:
                    correct_answer = correct_answers[0]['text']
                    correct_answer_id = correct_answers[0]['id']
                else:
                    # Fallback to first answer
                    correct_answer = question['answers'][0]['text']
                    correct_answer_id = question['answers'][0]['id']
            
            # Submit answer
            submit_data = {
                'session_id': session_id,
                'category_slug': category['slug'],  # Use the category we THINK we're in
                'question_id': question.get('id'),
                'question_text': question['text'],
                'selected_answer': correct_answer,
                'time_taken_seconds': 2
            }
            
            if correct_answer_id:
                submit_data['selected_answer_id'] = correct_answer_id
            
            submit_response = client.post(
                '/api/entertainment/quiz/game/submit_answer/',
                data=submit_data,
                format='json'
            )
            
            if submit_response.status_code == 200:
                submitted += 1
                is_correct = submit_response.data.get('submission', {}).get('is_correct')
                icon = "✅" if is_correct else "❌"
                if q_num <= 3 or not is_correct:  # Show first 3 or errors
                    print(f"   {icon} Q{q_num}: Submitted (Correct: {is_correct})")
            else:
                errors += 1
                print(f"   ❌ Q{q_num}: ERROR - {submit_response.status_code}")
                if q_num <= 3:
                    print(f"      {submit_response.data}")
        
        print(f"\n📊 Category {idx} Results: {submitted} submitted, {errors} errors")
        
        # Small delay between categories
        import time
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


def test_all_categories_at_once():
    """Test loading all categories at once (original behavior)"""
    print("\n" + "=" * 80)
    print("TEST: All Categories At Once (Original Behavior)")
    print("=" * 80)
    
    client = APIClient()
    client.credentials(HTTP_HOST='localhost:8000')
    session_token = str(uuid.uuid4())
    
    # Start Session - this should return ALL questions
    print("\n📍 Starting Session (should return all questions)...")
    response = client.post(
        '/api/entertainment/quiz/game/start_session/',
        data={
            'player_name': 'AllAtOncePlayer',
            'session_token': session_token,
            'is_tournament_mode': False
        },
        format='json'
    )
    
    if response.status_code != 201:
        print(f"❌ Failed: {response.status_code}")
        return
    
    session_data = response.data
    categories = session_data.get('categories', [])
    
    print(f"✅ Session started")
    print(f"\n📋 Categories ({len(categories)}):")
    
    for cat in categories:
        math_indicator = "🔢" if cat.get('is_math_category') else "📝"
        print(f"   {math_indicator} {cat['order']}. {cat['name']} "
              f"(Math: {cat.get('is_math_category', False)})")
    
    print("\n" + "=" * 80)


def check_player_progress():
    """Check the player progress tracking"""
    print("\n" + "=" * 80)
    print("CHECKING PLAYER PROGRESS TRACKING")
    print("=" * 80)
    
    # Get recent sessions
    recent_sessions = QuizSession.objects.order_by('-started_at')[:3]
    
    for session in recent_sessions:
        print(f"\n📊 Session: {session.player_name}")
        print(f"   Token: {session.session_token[:20]}...")
        print(f"   Started: {session.started_at}")
        
        # Get player progress
        try:
            progress = QuizPlayerProgress.objects.get(
                session_token=session.session_token,
                quiz=session.quiz
            )
            
            print(f"   Seen Question IDs:")
            for cat_slug, question_ids in progress.seen_question_ids.items():
                print(f"      {cat_slug}: {len(question_ids)} questions seen")
            
            if hasattr(progress, 'seen_math_combos') and progress.seen_math_combos:
                print(f"   Seen Math Combos: {len(progress.seen_math_combos)}")
        except QuizPlayerProgress.DoesNotExist:
            print(f"   ⚠️ No progress tracking found")


if __name__ == '__main__':
    print("\n" + "🔍" * 40)
    print("QUIZ CATEGORY LOADING BUG TEST")
    print("Testing: Math at Position 4 - Frontend Behavior Simulation")
    print("🔍" * 40)
    
    # Setup
    categories = setup_categories_with_math_at_4()
    
    # Run tests
    test_category_by_category_loading()
    
    # Alternative test
    # test_all_categories_at_once()
    
    # Check state
    check_player_progress()
    
    print("\n" + "="*80)
    print("SUMMARY & FRONTEND INSTRUCTIONS")
    print("="*80)
    print("""
🔍 EXPECTED BUG BEHAVIOR:

The test simulates the frontend calling fetch_category_questions for each 
category in sequence. Based on the code structure, here's what happens:

CATEGORY 1 (Classic Trivia): ✅ WORKS FINE
- First category loads correctly
- Questions are fetched, tracked, and submitted
- No issues observed

CATEGORY 2+ (Odd One Out, Fill the Blank, Math, etc.): ⚠️ STARTS GETTING CRAZY
- Category metadata might not match expected category
- Questions might be from wrong category
- Order field inconsistencies
- Math questions appearing in non-math categories or vice versa

🐛 ROOT CAUSE:
The fetch_category_questions endpoint relies on the category_slug parameter,
but there might be:
1. Caching issues with QuizCategory.objects.get(slug=...)
2. Player progress tracking mixing up category slugs
3. Session state not properly tracking current category
4. Race conditions when switching between categories

📝 FRONTEND FIX INSTRUCTIONS:

IF THE TEST PASSES (no errors detected):
✅ Backend is working correctly
✅ Continue with current frontend implementation
✅ Make sure frontend sends correct category_slug for each fetch

IF THE TEST FAILS (mismatches detected):
❌ Bug confirmed in backend
❌ Frontend should implement these workarounds:

1. **Add Category Validation:**
   ```javascript
   const validateCategoryResponse = (expectedCategory, response) => {
     const receivedCategory = response.category;
     if (receivedCategory.slug !== expectedCategory.slug) {
       console.error('Category mismatch!', {
         expected: expectedCategory.slug,
         received: receivedCategory.slug
       });
       // Retry or show error to user
       return false;
     }
     return true;
   };
   ```

2. **Verify Questions Belong to Category:**
   ```javascript
   const validateQuestions = (expectedCategorySlug, questions) => {
     const invalidQuestions = questions.filter(
       q => q.category_slug !== expectedCategorySlug
     );
     if (invalidQuestions.length > 0) {
       console.error('Questions from wrong category!', invalidQuestions);
       return false;
     }
     return true;
   };
   ```

3. **Add Retry Logic:**
   ```javascript
   const fetchCategoryWithRetry = async (sessionId, categorySlug, maxRetries = 3) => {
     for (let i = 0; i < maxRetries; i++) {
       const response = await fetchCategoryQuestions(sessionId, categorySlug);
       if (validateCategoryResponse({ slug: categorySlug }, response)) {
         return response;
       }
       console.warn(`Retry ${i + 1}/${maxRetries} for category ${categorySlug}`);
       await sleep(500); // Wait 500ms before retry
     }
     throw new Error(`Failed to fetch correct category after ${maxRetries} retries`);
   };
   ```

4. **Clear Session Between Categories (Nuclear Option):**
   ```javascript
   // If backend is really broken, create new session for each category
   // (Not recommended, but works as last resort)
   const startNewSessionForCategory = async (categorySlug) => {
     const newToken = generateUUID();
     const session = await startSession(playerName, newToken);
     return { session, token: newToken };
   };
   ```

🚨 CRITICAL: Report any mismatches found in this test to backend team!
    """)
