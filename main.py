INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
]

AUTH_USER_MODEL = "core.CustomUser"
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now

# Custom User Model
class CustomUser(AbstractUser):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('participant', 'Participant'),
        ('judge', 'Judge'),
    )
    role = models.CharField(max_length=20, choices=USER_ROLES, default='participant')

# Problem Model
class Problem(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    test_cases = models.JSONField()  # {"inputs": ["1 2"], "outputs": ["3"]}
    created_at = models.DateTimeField(auto_now_add=True)

# Submission Model
class Submission(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20)
    result = models.CharField(max_length=50, default="Pending")  # Passed/Failed
    created_at = models.DateTimeField(auto_now_add=True)

# Contest Model
class Contest(models.Model):
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    problems = models.ManyToManyField(Problem)
    participants = models.ManyToManyField(CustomUser)

    def is_active(self):
        return self.start_time <= now() <= self.end_time

# Leaderboard Model
class Leaderboard(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
from rest_framework import serializers
from .models import CustomUser, Problem, Submission, Contest, Leaderboard

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = '__all__'

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = '__all__'

class ContestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = '__all__'

class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser, Problem, Submission, Contest, Leaderboard
from .serializers import UserSerializer, ProblemSerializer, SubmissionSerializer, ContestSerializer, LeaderboardSerializer
import subprocess

# User Registration
class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

# List Problems
class ProblemListView(generics.ListCreateAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

# Submit Code for Evaluation
class SubmitCodeView(generics.CreateAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        submission = Submission.objects.create(
            user=request.user,
            problem_id=request.data['problem'],
            code=request.data['code'],
            language=request.data['language']
        )

        # Simple Code Execution Sandbox (Mocked)
        try:
            process = subprocess.run(
                ["python3", "-c", submission.code],
                capture_output=True, text=True, timeout=5
            )
            output = process.stdout.strip()
            expected_output = submission.problem.test_cases["outputs"][0]

            submission.result = "Passed" if output == expected_output else "Failed"
            submission.save()

        except Exception as e:
            submission.result = "Error"
            submission.save()

        return Response({"result": submission.result}, status=status.HTTP_201_CREATED)

# View Leaderboard
class LeaderboardView(generics.ListAPIView):
    queryset = Leaderboard.objects.order_by('-score')
    serializer_class = LeaderboardSerializer

# Manage Contests
class ContestListView(generics.ListCreateAPIView):
    queryset = Contest.objects.all()
    serializer_class = ContestSerializer
from django.urls import path
from .views import RegisterUserView, ProblemListView, SubmitCodeView, LeaderboardView, ContestListView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('problems/', ProblemListView.as_view(), name='problem-list'),
    path('submit/', SubmitCodeView.as_view(), name='submit-code'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('contests/', ContestListView.as_view(), name='contest-list'),
]
from django.contrib import admin
from .models import CustomUser, Problem, Submission, Contest, Leaderboard

admin.site.register(CustomUser)
admin.site.register(Problem)
admin.site.register(Submission)
admin.site.register(Contest)
admin.site.register(Leaderboard)



