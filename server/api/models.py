from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    leetcode_username = models.CharField(max_length=100, blank=True)
    streak_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Question(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=20)  # Easy, Medium, Hard
    topic = models.CharField(max_length=100, blank=True)
    companies = models.JSONField(default=list)
    leetcode_link = models.URLField()
    why_it_matters = models.CharField(max_length=255, blank=True)
    # New fields for LeetCode-style experience
    constraints = models.TextField(blank=True, default="")
    examples = models.JSONField(default=list, blank=True)
    # Each example: {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "..."}
    test_cases = models.JSONField(default=list, blank=True)
    # Each test case: {"input": "nums = [2,7,11,15], target = 9", "expected_output": "[0,1]"}
    starter_code = models.JSONField(default=dict, blank=True)
    # {"python": "class Solution:\n    def twoSum(self, ...):", "cpp": "...", "java": "...", "javascript": "..."}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.CharField(max_length=20)
    status = models.CharField(max_length=50)  # Accepted, Rejected, Pending
    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question.title} ({self.status})"

class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='interview')
    chat_history = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    mock_interview = models.ForeignKey('MockInterview', on_delete=models.CASCADE, null=True, blank=True, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview: {self.user.username} - {self.question.title}"

class MockInterview(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mock_interviews')
    topic = models.CharField(max_length=50)
    subtopics = models.JSONField(default=list, blank=True)
    difficulty = models.CharField(max_length=20)
    time_limit = models.IntegerField(default=30)
    questions = models.ManyToManyField(Question, related_name='mock_interviews', blank=True)
    current_question_index = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    performance_summary = models.TextField(blank=True, default="")  # LLM-generated final report
    total_time_spent = models.IntegerField(default=0)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MockInterview: {self.user.username} - {self.topic} ({self.status})"


class QuestionPerformance(models.Model):
    """Tracks per-question performance within a mock interview."""
    mock_interview = models.ForeignKey(MockInterview, on_delete=models.CASCADE, related_name='performances')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')  # pending, accepted, wrong_answer, skipped
    time_spent = models.IntegerField(default=0)  # seconds spent on this question
    code = models.TextField(blank=True, default="")
    language = models.CharField(max_length=20, blank=True, default="python")
    interview_brief = models.TextField(blank=True, default="")  # AI-generated summary of interview for this question
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question.title} - {self.status}"
