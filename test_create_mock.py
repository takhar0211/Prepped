import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Question, MockInterview, User

# Get first user
user = User.objects.first()
print(f"Testing for user: {user.username}")

topic = "dsa"
difficulty = "Easy"
num_questions = 3

available_questions = Question.objects.all()
diff_questions = available_questions.filter(difficulty__iexact=difficulty)

questions = list(diff_questions.order_by('?')[:num_questions])
print(f"Selected {len(questions)} questions:")
for q in questions:
    print(f"- {q.title}")

mock = MockInterview.objects.create(
    user=user,
    topic=topic,
    difficulty=difficulty,
)

for question in questions:
    mock.questions.add(question)

print(f"Mock Interview created successfully: ID {mock.id}")
