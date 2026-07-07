from django.urls import path
from .views import (
    SignupView, LoginView, LogoutView, CurrentUserView, ProfileStatsView,
    RecommendQuestionsView, QuestionDetailView,
    RunCodeView, SubmitCodeView, InterviewChatView,
    GenerateInterviewView, MockInterviewDetailView,
    SaveQuestionPerformanceView, FinishInterviewView,
    SpeechToTextView,
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('me/stats/', ProfileStatsView.as_view(), name='profile-stats'),
    path('recommendations/', RecommendQuestionsView.as_view(), name='recommendations'),
    path('question/<int:question_id>/', QuestionDetailView.as_view(), name='question-detail'),
    path('run/', RunCodeView.as_view(), name='run-code'),
    path('submit/', SubmitCodeView.as_view(), name='submit-code'),
    path('interview/<int:session_id>/', InterviewChatView.as_view(), name='interview'),
    # Mock Interview
    path('mock-interview/generate/', GenerateInterviewView.as_view(), name='generate-interview'),
    path('mock-interview/<int:mock_id>/', MockInterviewDetailView.as_view(), name='mock-interview-detail'),
    path('mock-interview/<int:mock_id>/performance/<int:question_id>/', SaveQuestionPerformanceView.as_view(), name='save-performance'),
    path('mock-interview/<int:mock_id>/finish/', FinishInterviewView.as_view(), name='finish-interview'),
    path('speech-to-text/', SpeechToTextView.as_view(), name='speech-to-text'),
]
