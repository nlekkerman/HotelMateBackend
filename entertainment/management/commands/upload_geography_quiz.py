"""
Management command to upload Geography quiz category and questions
Usage: python manage.py upload_geography_quiz
"""
import json
from django.core.management.base import BaseCommand
from entertainment.models import QuizCategory, QuizQuestion


class Command(BaseCommand):
    help = 'Upload Geography quiz category and questions from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?',
            default=r'c:\Users\nlekk\Desktop\quiz\GEOGRAPHY.txt',
            help='Path to the Geography JSON file'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Remove JSON comments (lines starting with /* or //)
                content = f.read()
                # Simple comment removal
                lines = []
                for line in content.split('\n'):
                    stripped = line.strip()
                    is_comment = (
                        stripped.startswith('/*') or
                        stripped.startswith('//')
                    )
                    if not is_comment:
                        lines.append(line)
                clean_content = '\n'.join(lines)
                
                data = json.loads(clean_content)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {e}'))
            return
        
        category_name = data.get('category')
        questions_data = data.get('questions', [])
        
        # Create or get category
        category, created = QuizCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'slug': category_name.lower(),
                'description': f'Questions about {category_name}',
                'icon': '🌍',
                'color': '#10B981',
                'is_active': True,
                'display_order': 1
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created category: {category_name}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'⚠ Category already exists: {category_name}'
            ))
        
        # Upload questions
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for q_data in questions_data:
            q_type = q_data.get('type')
            difficulty = q_data.get('difficulty', 'medium')
            
            # Skip non-trivia questions for now (true_false, finish_sentence)
            if q_type != 'trivia':
                skipped_count += 1
                continue
            
            question_text = q_data.get('question')
            options = q_data.get('options', [])
            correct_index = q_data.get('correct_index')
            
            if len(options) != 4:
                msg = (
                    f'⚠ Skipping question with {len(options)} '
                    f'options: {question_text[:50]}...'
                )
                self.stdout.write(self.style.WARNING(msg))
                skipped_count += 1
                continue
            
            # Map index to letter (0=A, 1=B, 2=C, 3=D)
            correct_answer = ['A', 'B', 'C', 'D'][correct_index]
            
            # Check if question already exists
            existing = QuizQuestion.objects.filter(
                category=category,
                question_text=question_text
            ).first()
            
            if existing:
                # Update existing question
                existing.difficulty = difficulty
                existing.option_a = options[0]
                existing.option_b = options[1]
                existing.option_c = options[2]
                existing.option_d = options[3]
                existing.correct_answer = correct_answer
                existing.is_active = True
                existing.save()
                updated_count += 1
            else:
                # Create new question
                QuizQuestion.objects.create(
                    category=category,
                    question_text=question_text,
                    difficulty=difficulty,
                    option_a=options[0],
                    option_b=options[1],
                    option_c=options[2],
                    option_d=options[3],
                    correct_answer=correct_answer,
                    explanation='',
                    points=10,
                    is_active=True
                )
                created_count += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            '\n✓ Upload complete!'
        ))
        self.stdout.write(f'  Created: {created_count} questions')
        self.stdout.write(f'  Updated: {updated_count} questions')
        self.stdout.write(f'  Skipped: {skipped_count} questions')
        
        total_questions = QuizQuestion.objects.filter(
            category=category,
            is_active=True
        ).count()
        msg = (
            f'\n✓ Total {category_name} questions in database: '
            f'{total_questions}'
        )
        self.stdout.write(self.style.SUCCESS(msg))
