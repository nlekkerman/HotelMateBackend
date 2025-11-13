"""
Test Quiz Game Logic - Current Implementation
Tests the new category-based quiz system with dynamic math questions
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import override_settings
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizAnswer,
    QuizSession, QuizSubmission, QuizTournament
)
from entertainment.views import QuizViewSet, QuizCategoryViewSet, QuizGameViewSet
import uuid


class QuizGameAPITests(TestCase):
    """Test the Quiz Game API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Get or create the main quiz
        self.quiz, created = Quiz.objects.get_or_create(
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
        
        # Get or create categories
        self.trivia_category, created = QuizCategory.objects.get_or_create(
            slug='classic-trivia',
            defaults={
                'name': 'Classic Trivia',
                'description': 'General knowledge questions',
                'order': 1,
                'is_math_category': False,
                'is_active': True
            }
        )
        
        self.math_category, created = QuizCategory.objects.get_or_create(
            slug='dynamic-math',
            defaults={
                'name': 'Dynamic Math',
                'description': 'Math challenges',
                'order': 2,
                'is_math_category': True,
                'is_active': True
            }
        )
        
        self.oddone_category, created = QuizCategory.objects.get_or_create(
            slug='odd-one-out',
            defaults={
                'name': 'Odd One Out',
                'description': 'Find the odd one',
                'order': 3,
                'is_math_category': False,
                'is_active': True
            }
        )
        
        # Create trivia questions (only if they don't exist)
        existing_trivia = QuizQuestion.objects.filter(
            category=self.trivia_category
        ).count()
        
        if existing_trivia < 15:
            for i in range(15 - existing_trivia):
                question = QuizQuestion.objects.create(
                    category=self.trivia_category,
                    text=f'Trivia Question {i+1}?',
                    is_active=True
                )
                
                # Create 4 answers (1 correct, 3 wrong)
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
        
        # Create odd-one-out questions (only if they don't exist)
        existing_oddone = QuizQuestion.objects.filter(
            category=self.oddone_category
        ).count()
        
        if existing_oddone < 15:
            for i in range(15 - existing_oddone):
                question = QuizQuestion.objects.create(
                    category=self.oddone_category,
                    text=f'Odd One Out Question {i+1}?',
                    is_active=True
                )
                
                QuizAnswer.objects.create(
                    question=question,
                    text=f'Correct Odd {i+1}',
                    is_correct=True,
                    order=0
                )
                for j in range(3):
                    QuizAnswer.objects.create(
                        question=question,
                        text=f'Normal Item {j+1}',
                        is_correct=False,
                        order=j+1
                    )
        
        print("✅ Test setup complete")
        print(f"   Quiz: {self.quiz.title}")
        print(f"   Categories: {QuizCategory.objects.filter(is_active=True).count()}")
        print(f"   Questions: {QuizQuestion.objects.filter(is_active=True).count()}")
    
    def test_fetch_quiz_list(self):
        """Test fetching list of quizzes"""
        print("\n" + "="*70)
        print("TEST: Fetch Quiz List")
        print("="*70)
        
        response = self.client.get('/api/v1/entertainment/quizzes/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.data, indent=2)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        print("✅ Quiz list fetched successfully")
    
    def test_fetch_quiz_detail(self):
        """Test fetching quiz details"""
        print("\n" + "="*70)
        print("TEST: Fetch Quiz Detail")
        print("="*70)
        
        response = self.client.get(f'/api/v1/entertainment/quizzes/{self.quiz.slug}/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Quiz Title: {response.data.get('title')}")
        print(f"Questions per Category: {response.data.get('questions_per_category')}")
        print(f"Turbo Threshold: {response.data.get('turbo_mode_threshold')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'guessticulator')
        
        print("✅ Quiz detail fetched successfully")
    
    def test_fetch_categories(self):
        """Test fetching quiz categories"""
        print("\n" + "="*70)
        print("TEST: Fetch Quiz Categories")
        print("="*70)
        
        response = self.client.get('/api/v1/entertainment/quiz-categories/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Categories Count: {len(response.data)}")
        
        for category in response.data:
            print(f"\n  Category: {category['name']}")
            print(f"    Slug: {category['slug']}")
            print(f"    Order: {category['order']}")
            print(f"    Is Math: {category.get('is_math_category', False)}")
            print(f"    Questions: {category.get('question_count', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        print("\n✅ Categories fetched successfully")
    
    def test_start_session(self):
        """Test starting a new game session"""
        print("\n" + "="*70)
        print("TEST: Start Game Session")
        print("="*70)
        
        session_token = str(uuid.uuid4())
        
        data = {
            'player_name': 'TestPlayer',
            'session_token': session_token,
            'is_tournament_mode': False
        }
        
        response = self.client.post(
            '/api/v1/entertainment/quiz/game/start_session/',
            data=data,
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Session ID: {response.data.get('session', {}).get('id')}")
        print(f"Player: {response.data.get('session', {}).get('player_name')}")
        print(f"Current Category: {response.data.get('current_category', {}).get('name')}")
        print(f"Questions Count: {len(response.data.get('questions', []))}")
        print(f"Total Categories: {response.data.get('total_categories')}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['session']['player_name'], 'TestPlayer')
        self.assertEqual(len(response.data['questions']), 10)
        
        # Check first question structure
        first_question = response.data['questions'][0]
        print(f"\nFirst Question:")
        print(f"  Text: {first_question['text']}")
        print(f"  Answers: {len(first_question['answers'])}")
        
        print("\n✅ Session started successfully")
        return response.data
    
    def test_start_session_with_math_category(self):
        """Test that math questions are generated dynamically"""
        print("\n" + "="*70)
        print("TEST: Dynamic Math Question Generation")
        print("="*70)
        
        # Make math category first
        self.math_category.order = 0
        self.math_category.save()
        
        session_token = str(uuid.uuid4())
        
        data = {
            'player_name': 'MathPlayer',
            'session_token': session_token,
            'is_tournament_mode': False
        }
        
        response = self.client.post(
            '/api/v1/entertainment/quiz/game/start_session/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        questions = response.data.get('questions', [])
        print(f"Math Questions Generated: {len(questions)}")
        
        # Check math question structure
        for i, q in enumerate(questions[:3], 1):
            print(f"\n  Math Question {i}:")
            print(f"    Text: {q['text']}")
            print(f"    Question Data: {q.get('question_data')}")
            self.assertIn('question_data', q)
            self.assertIn('correct_answer', q['question_data'])
        
        print("\n✅ Math questions generated successfully")
    
    def test_submit_answer_correct(self):
        """Test submitting a correct answer"""
        print("\n" + "="*70)
        print("TEST: Submit Correct Answer")
        print("="*70)
        
        # Start session
        session_data = self.test_start_session()
        session_id = session_data['session']['id']
        question = session_data['questions'][0]
        
        # Find correct answer
        correct_answer = next(
            (a for a in question['answers'] if a['text'] == 'Correct Answer 1'),
            question['answers'][0]
        )
        
        data = {
            'session_id': session_id,
            'category_slug': session_data['current_category']['slug'],
            'question_id': question['id'],
            'question_text': question['text'],
            'selected_answer': correct_answer['text'],
            'selected_answer_id': correct_answer['id'],
            'time_taken_seconds': 2
        }
        
        response = self.client.post(
            '/api/v1/entertainment/quiz/game/submit_answer/',
            data=data,
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Success: {response.data.get('success')}")
        print(f"Is Correct: {response.data.get('submission', {}).get('is_correct')}")
        print(f"Points Awarded: {response.data.get('submission', {}).get('points_awarded')}")
        print(f"Session Score: {response.data.get('session_updated', {}).get('score')}")
        print(f"Consecutive Correct: {response.data.get('session_updated', {}).get('consecutive_correct')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['submission']['is_correct'])
        self.assertGreater(response.data['submission']['points_awarded'], 0)
        
        print("✅ Correct answer submitted successfully")
    
    def test_submit_answer_wrong(self):
        """Test submitting a wrong answer"""
        print("\n" + "="*70)
        print("TEST: Submit Wrong Answer")
        print("="*70)
        
        # Start session
        session_data = self.test_start_session()
        session_id = session_data['session']['id']
        question = session_data['questions'][0]
        
        # Find wrong answer
        wrong_answer = next(
            (a for a in question['answers'] if a['text'].startswith('Wrong')),
            question['answers'][1]
        )
        
        data = {
            'session_id': session_id,
            'category_slug': session_data['current_category']['slug'],
            'question_id': question['id'],
            'question_text': question['text'],
            'selected_answer': wrong_answer['text'],
            'selected_answer_id': wrong_answer['id'],
            'time_taken_seconds': 3
        }
        
        response = self.client.post(
            '/api/v1/entertainment/quiz/game/submit_answer/',
            data=data,
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Is Correct: {response.data.get('submission', {}).get('is_correct')}")
        print(f"Points Awarded: {response.data.get('submission', {}).get('points_awarded')}")
        print(f"Consecutive Correct Reset: {response.data.get('session_updated', {}).get('consecutive_correct')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['submission']['is_correct'])
        self.assertEqual(response.data['submission']['points_awarded'], 0)
        self.assertEqual(response.data['session_updated']['consecutive_correct'], 0)
        
        print("✅ Wrong answer submitted successfully")
    
    def test_turbo_mode_activation(self):
        """Test turbo mode activation after 5 consecutive correct answers"""
        print("\n" + "="*70)
        print("TEST: Turbo Mode Activation")
        print("="*70)
        
        # Start session
        session_data = self.test_start_session()
        session_id = session_data['session']['id']
        
        # Submit 5 correct answers
        for i, question in enumerate(session_data['questions'][:5], 1):
            correct_answer = next(
                (a for a in question['answers'] if 'Correct' in a['text']),
                question['answers'][0]
            )
            
            data = {
                'session_id': session_id,
                'category_slug': session_data['current_category']['slug'],
                'question_id': question['id'],
                'question_text': question['text'],
                'selected_answer': correct_answer['text'],
                'selected_answer_id': correct_answer['id'],
                'time_taken_seconds': 1
            }
            
            response = self.client.post(
                '/api/v1/entertainment/quiz/game/submit_answer/',
                data=data,
                format='json'
            )
            
            consecutive = response.data.get('session_updated', {}).get('consecutive_correct')
            is_turbo = response.data.get('session_updated', {}).get('is_turbo_active')
            
            print(f"\nAnswer {i}:")
            print(f"  Consecutive Correct: {consecutive}")
            print(f"  Turbo Active: {is_turbo}")
            
            if i >= 5:
                self.assertTrue(is_turbo, "Turbo mode should be active after 5 correct answers")
        
        print("\n✅ Turbo mode activated successfully")
    
    def test_models_and_logic(self):
        """Test model methods and business logic"""
        print("\n" + "="*70)
        print("TEST: Model Methods and Logic")
        print("="*70)
        
        # Create a session
        session = QuizSession.objects.create(
            quiz=self.quiz,
            session_token=str(uuid.uuid4()),
            player_name='ModelTestPlayer',
            score=0
        )
        
        print(f"Session Created: {session}")
        
        # Test submission point calculation
        question = QuizQuestion.objects.filter(category=self.trivia_category).first()
        
        # Test normal mode points
        submission1 = QuizSubmission.objects.create(
            session=session,
            category=self.trivia_category,
            question=question,
            question_text=question.text,
            selected_answer='Correct',
            correct_answer='Correct',
            is_correct=True,
            time_taken_seconds=1,
            was_turbo_active=False
        )
        
        points_normal = submission1.calculate_points()
        print(f"\nNormal Mode Points (1 sec): {points_normal}")
        self.assertEqual(points_normal, 5)
        
        # Test turbo mode points
        submission2 = QuizSubmission.objects.create(
            session=session,
            category=self.trivia_category,
            question=question,
            question_text=question.text,
            selected_answer='Correct',
            correct_answer='Correct',
            is_correct=True,
            time_taken_seconds=1,
            was_turbo_active=True
        )
        
        points_turbo = submission2.calculate_points()
        print(f"Turbo Mode Points (1 sec): {points_turbo}")
        self.assertEqual(points_turbo, 10)
        
        # Test wrong answer
        submission3 = QuizSubmission.objects.create(
            session=session,
            category=self.trivia_category,
            question=question,
            question_text=question.text,
            selected_answer='Wrong',
            correct_answer='Correct',
            is_correct=False,
            time_taken_seconds=2,
            was_turbo_active=False
        )
        
        points_wrong = submission3.calculate_points()
        print(f"Wrong Answer Points: {points_wrong}")
        self.assertEqual(points_wrong, 0)
        
        # Test session completion
        session.complete_session()
        print(f"\nSession Completed: {session.is_completed}")
        print(f"Duration: {session.duration_formatted}")
        
        self.assertTrue(session.is_completed)
        self.assertIsNotNone(session.finished_at)
        
        print("\n✅ Model logic tested successfully")


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("QUIZ GAME API TESTS - Current Implementation")
    print("Category-based system with dynamic math questions")
    print("="*70)
    
    # Create test suite
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.test.runner import DiscoverRunner
    
    setup_test_environment()
    runner = DiscoverRunner(verbosity=2)
    
    # Run specific test class
    suite = runner.build_suite(test_labels=None)
    result = runner.run_suite(suite)
    
    teardown_test_environment()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
                print(f"    {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
                print(f"    {traceback}")


if __name__ == '__main__':
    import sys
    from io import StringIO
    
    # Run the tests
    test_case = QuizGameAPITests()
    test_case.setUp()
    
    print("\n" + "="*70)
    print("RUNNING INDIVIDUAL TEST METHODS")
    print("="*70)
    
    try:
        test_case.test_fetch_quiz_list()
        test_case.test_fetch_quiz_detail()
        test_case.test_fetch_categories()
        test_case.test_start_session()
        test_case.test_start_session_with_math_category()
        test_case.test_submit_answer_correct()
        test_case.test_submit_answer_wrong()
        test_case.test_turbo_mode_activation()
        test_case.test_models_and_logic()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
