from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import json
import logging
import requests
from django.conf import settings
from django.db.models import Q
from .models import UserProfile, Question, Submission, InterviewSession, MockInterview, QuestionPerformance
from .serializers import UserSerializer, QuestionSerializer, SubmissionSerializer, InterviewSessionSerializer, MockInterviewSerializer, QuestionPerformanceSerializer
from .utils import get_leetcode_submissions, validate_code_with_llm, generate_test_cases_for_question, interview_follow_up, generate_performance_report, generate_interview_questions

logger = logging.getLogger(__name__)



class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Bypass CSRF checks for the API


# ══════════════════════════════════════════════════════════════
# AUTH VIEWS
# ══════════════════════════════════════════════════════════════

class SignupView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        leetcode_username = request.data.get('leetcode_username', '')

        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, leetcode_username=leetcode_username)

        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return Response(UserSerializer(user).data)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})


class CurrentUserView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProfileStatsView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Questions logic
        # Count all individual submission attempts
        questions_attempted = Submission.objects.filter(user=user).values('question').distinct().count()
        questions_solved = Submission.objects.filter(user=user, status='Accepted').values('question').distinct().count()

        # Mock interviews logic
        all_mocks = MockInterview.objects.filter(user=user).order_by('-created_at')
        mocks_attempted = all_mocks.count()
        mocks_completed = all_mocks.filter(status='completed').count()
        
        # Get recent mock history
        recent_mocks = []
        for m in all_mocks[:5]:
            score = 0
            if m.performance_summary:
                try:
                    summary_data = json.loads(m.performance_summary)
                    score = summary_data.get('overall_score', 0)
                except Exception:
                    pass
            
            recent_mocks.append({
                'id': m.id,
                'topic': m.topic,
                'difficulty': m.difficulty,
                'status': m.status,
                'created_at': m.created_at,
                'score': score
            })

        return Response({
            'questions': {
                'attempted': questions_attempted,
                'solved': questions_solved,
            },
            'mocks': {
                'attempted': mocks_attempted,
                'completed': mocks_completed,
            },
            'recent_history': recent_mocks
        })


# ══════════════════════════════════════════════════════════════
# QUESTION VIEWS
# ══════════════════════════════════════════════════════════════


class RecommendQuestionsView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        
        cache_key = f'user_recs_{request.user.id}'
        cached_recs = cache.get(cache_key)
        if cached_recs:
            return Response(cached_recs, status=status.HTTP_200_OK)

        profile = request.user.profile
        solved_lc, err = get_leetcode_submissions(profile.leetcode_username)
        solved_titles = [q['title'] for q in solved_lc] if solved_lc else []

        # Add questions solved in our platform too
        platform_solved = Submission.objects.filter(
            user=request.user, status='Accepted'
        ).values_list('question__title', flat=True)
        all_solved = list(set(solved_titles + list(platform_solved)))

        # Fetch 5 random unsolved DSA questions from DB
        available_questions = Question.objects.exclude(title__in=all_solved).exclude(
            Q(topic__icontains='sql') | 
            Q(topic__icontains='database') |
            Q(topic__icontains='subqueries') |
            Q(topic__icontains='system design') |
            Q(topic__icontains='system_design')
        )
        
        recs = list(available_questions.order_by('?')[:5])
        
        response_data = []
        for question in recs:
            response_data.append(QuestionSerializer(question).data)

        # Cache the recommendations for 1 hour
        cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data, status=status.HTTP_200_OK)


class QuestionDetailView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, question_id):
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

        # Auto-generate and cache 10 test cases if not already present
        if not question.test_cases or len(question.test_cases) < 10:
            generate_test_cases_for_question(question)
            question.refresh_from_db()

        return Response(QuestionSerializer(question).data)


# ══════════════════════════════════════════════════════════════
# CODE EXECUTION VIEWS
# ══════════════════════════════════════════════════════════════

class RunCodeView(views.APIView):
    """Run code against example test cases only (like LeetCode 'Run')"""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question_id = request.data.get('question_id')
        code = request.data.get('code', '')
        language = request.data.get('language', 'python')
        
        logger.info(f"[RunCode] Frontend Payload Received - Selected Language: {language}, Question ID: {question_id}")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

        # Use examples as test cases for "Run"
        examples_as_tests = [
            {"input": ex["input"], "expected_output": ex["output"]}
            for ex in (question.examples or [])
        ]

        if not examples_as_tests:
            return Response({'error': 'No examples available for this question'}, status=status.HTTP_400_BAD_REQUEST)

        result = validate_code_with_llm(code, language, examples_as_tests, question.description)

        return Response({
            'all_passed': result.all_passed,
            'test_results': [tr.model_dump() for tr in result.test_results],
            'error_message': result.error_message,
            'feedback': result.feedback if not result.all_passed else '',
        })


class SubmitCodeView(views.APIView):
    """Submit code — validates against ALL 10 cached test cases and triggers interview if passed"""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question_id = request.data.get('question_id')
        code = request.data.get('code', '')
        language = request.data.get('language', 'python')
        
        logger.info(f"[SubmitCode] Frontend Payload Received - Selected Language: {language}, Question ID: {question_id}")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure 10 test cases are cached in DB
        all_tests = generate_test_cases_for_question(question)

        if not all_tests:
            return Response({'error': 'No test cases available'}, status=status.HTTP_400_BAD_REQUEST)

        result = validate_code_with_llm(code, language, all_tests, question.description)

        # Save submission
        submission_status = 'Accepted' if result.all_passed else 'Wrong Answer'
        submission = Submission.objects.create(
            user=request.user,
            question=question,
            code=code,
            language=language,
            status=submission_status,
        )

        response_data = {
            'submission': SubmissionSerializer(submission).data,
            'all_passed': result.all_passed,
            'test_results': [tr.model_dump() for tr in result.test_results],
            'error_message': result.error_message,
            'feedback': result.feedback if not result.all_passed else '',
        }

        # If ALL test cases pass, create interview session and ask first question
        if result.all_passed:
            session = InterviewSession.objects.create(
                user=request.user,
                question=question,
                submission=submission,
                chat_history=[]
            )
            # Generate the first interviewer question
            ai_question = interview_follow_up(
                question.title,
                question.description,
                code,
                language,
                []
            )
            session.chat_history.append({'role': 'assistant', 'content': ai_question})
            session.save()

            response_data['interview_session_id'] = session.id
            response_data['initial_question'] = ai_question

        return Response(response_data)


# ══════════════════════════════════════════════════════════════
# INTERVIEW CHAT VIEW
# ══════════════════════════════════════════════════════════════

class InterviewChatView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = InterviewSession.objects.get(id=session_id, user=request.user)
        except InterviewSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message required'}, status=status.HTTP_400_BAD_REQUEST)

        session.chat_history.append({'role': 'user', 'content': user_message})

        # Generate AI response with full context
        ai_response = interview_follow_up(
            session.question.title,
            session.question.description,
            session.submission.code,
            session.submission.language,
            session.chat_history
        )

        session.chat_history.append({'role': 'assistant', 'content': ai_response})
        session.save()

        return Response({'chat_history': session.chat_history})


# ══════════════════════════════════════════════════════════════
# MOCK INTERVIEW VIEWS
# ══════════════════════════════════════════════════════════════

class GenerateInterviewView(views.APIView):
    """Generate a custom mock interview based on user's configuration."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        topic = request.data.get('topic', 'dsa')
        subtopics = request.data.get('subtopics', [])
        difficulty = request.data.get('difficulty', 'Medium')
        num_questions = min(int(request.data.get('num_questions', 3)), 5)
        time_limit = int(request.data.get('time_limit', 30))

        # Get user's solved questions to prevent duplicates
        profile = request.user.profile
        solved_lc, err = get_leetcode_submissions(profile.leetcode_username)
        solved_titles = [q['title'] for q in solved_lc] if solved_lc else []

        platform_solved = Submission.objects.filter(
            user=request.user, status='Accepted'
        ).values_list('question__title', flat=True)
        all_solved = list(set(solved_titles + list(platform_solved)))

        # Query DB instead of using LLM
        available_questions = Question.objects.exclude(title__in=all_solved)
        
        # Proper domain filtering
        topic_lower = topic.lower()
        if topic_lower == 'sql':
            available_questions = available_questions.filter(
                Q(topic__icontains='sql') | 
                Q(topic__icontains='database') |
                Q(topic__icontains='subqueries')
            )
        elif topic_lower == 'system_design' or topic_lower == 'system design':
            available_questions = available_questions.filter(
                Q(topic__icontains='system design') |
                Q(topic__icontains='system_design')
            )
        else:
            # Default to DSA: Exclude all SQL and System Design topics
            available_questions = available_questions.exclude(
                Q(topic__icontains='sql') | 
                Q(topic__icontains='database') |
                Q(topic__icontains='subqueries') |
                Q(topic__icontains='system design') |
                Q(topic__icontains='system_design')
            )
        
        # Try to match difficulty, but fallback if not enough
        if difficulty:
            diff_questions = available_questions.filter(difficulty__iexact=difficulty)
            if diff_questions.count() >= num_questions:
                available_questions = diff_questions
                
        questions = list(available_questions.order_by('?')[:num_questions])
        
        # Fallback to LLM if there aren't enough questions in the database
        if len(questions) < num_questions:
            needed = num_questions - len(questions)
            
            # Fetch from LLM
            generated_questions = generate_interview_questions(topic, subtopics, difficulty, needed, all_solved)
            
            for q_data in generated_questions:
                # Save the LLM generated question to the database so future users can fetch it instantly!
                slug = q_data.title.lower().replace(' ', '-')
                question_obj, created = Question.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'title': q_data.title,
                        'description': q_data.description,
                        'difficulty': q_data.difficulty,
                        'topic': q_data.topic,
                        'companies': q_data.companies,
                        'leetcode_link': q_data.leetcode_link,
                        'why_it_matters': q_data.why_it_matters,
                        'constraints': q_data.constraints,
                        'examples': [e.model_dump() for e in q_data.examples],
                        'test_cases': [t.model_dump() for t in q_data.test_cases],
                        'starter_code': q_data.starter_code.model_dump(),
                    }
                )
                questions.append(question_obj)

                # Trigger test case generation for the new question
                generate_test_cases_for_question(question_obj)
                
            # If after the fallback we STILL don't have enough (e.g. LLM failed)
            if len(questions) == 0:
                return Response(
                    {'error': f'Failed to generate or fetch enough {topic.upper()} questions. Please try again.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create MockInterview
        mock = MockInterview.objects.create(
            user=request.user,
            topic=topic,
            subtopics=subtopics,
            difficulty=difficulty,
            time_limit=time_limit,
        )

        # Link questions to mock interview and create performance records
        for question in questions:
            mock.questions.add(question)
            # Create a performance tracker for each question
            QuestionPerformance.objects.create(
                mock_interview=mock,
                question=question,
            )

        return Response(MockInterviewSerializer(mock).data, status=status.HTTP_201_CREATED)


class MockInterviewDetailView(views.APIView):
    """Get details of a mock interview session."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, mock_id):
        try:
            mock = MockInterview.objects.get(id=mock_id, user=request.user)
        except MockInterview.DoesNotExist:
            return Response({'error': 'Interview not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MockInterviewSerializer(mock).data)

    def patch(self, request, mock_id):
        """Update current question index or status."""
        try:
            mock = MockInterview.objects.get(id=mock_id, user=request.user)
        except MockInterview.DoesNotExist:
            return Response({'error': 'Interview not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'current_question_index' in request.data:
            mock.current_question_index = request.data['current_question_index']
        if 'status' in request.data:
            mock.status = request.data['status']
        mock.save()
        return Response(MockInterviewSerializer(mock).data)


class SaveQuestionPerformanceView(views.APIView):
    """Save performance data for a specific question in a mock interview."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mock_id, question_id):
        try:
            perf = QuestionPerformance.objects.get(
                mock_interview_id=mock_id,
                question_id=question_id,
                mock_interview__user=request.user
            )
        except QuestionPerformance.DoesNotExist:
            return Response({'error': 'Performance record not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'status' in request.data:
            perf.status = request.data['status']
        if 'time_spent' in request.data:
            perf.time_spent = request.data['time_spent']
        if 'code' in request.data:
            perf.code = request.data['code']
        if 'language' in request.data:
            perf.language = request.data['language']
        if 'interview_brief' in request.data:
            perf.interview_brief = request.data['interview_brief']
        if 'attempts' in request.data:
            perf.attempts = request.data['attempts']
        perf.save()
        return Response(QuestionPerformanceSerializer(perf).data)


class FinishInterviewView(views.APIView):
    """Finish a mock interview — instantly marks as completed without generating a report."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mock_id):
        try:
            mock = MockInterview.objects.get(id=mock_id, user=request.user)
        except MockInterview.DoesNotExist:
            return Response({'error': 'Interview not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'total_time_spent' in request.data:
            mock.total_time_spent = request.data['total_time_spent']

        mock.status = 'completed'
        mock.save()

        return Response(MockInterviewSerializer(mock).data)


class GenerateReportView(views.APIView):
    """Generate an LLM-based performance report on demand. Caches the result."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mock_id):
        try:
            mock = MockInterview.objects.get(id=mock_id, user=request.user)
        except MockInterview.DoesNotExist:
            return Response({'error': 'Interview not found'}, status=status.HTTP_404_NOT_FOUND)

        # If report already exists, return it instantly (cached)
        if mock.performance_summary:
            try:
                cached_report = json.loads(mock.performance_summary)
                return Response({'report': cached_report, 'cached': True})
            except json.JSONDecodeError:
                pass  # Corrupted cache — regenerate

        # Collect performance data for report
        perfs = QuestionPerformance.objects.filter(mock_interview=mock).select_related('question')
        perf_data = []
        for p in perfs:
            perf_data.append({
                'title': p.question.title,
                'status': p.status,
                'time_spent': p.time_spent,
                'attempts': p.attempts,
                'language': p.language,
                'interview_brief': p.interview_brief,
            })

        # Generate LLM-based report
        report = generate_performance_report(mock.topic, mock.difficulty, perf_data)

        # Cache the report permanently
        mock.performance_summary = json.dumps(report)
        mock.save()

        return Response({'report': report, 'cached': False})


class SpeechToTextView(views.APIView):
    """Proxy endpoint for Sarvam AI Speech-to-Text API"""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_file = request.FILES.get('file')
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

        url = "https://api.sarvam.ai/speech-to-text"
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY
        }
        
        # Sarvam expects multipart/form-data
        files = {
            'file': (audio_file.name, audio_file.read(), audio_file.content_type)
        }
        data = {
            'model': 'saaras:v3',
            'mode': 'transcribe'
        }

        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return Response({'transcript': result.get('transcript', '')})
            else:
                return Response(
                    {'error': f'Sarvam API error: {response.text}'}, 
                    status=response.status_code
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
