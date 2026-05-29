from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Test, Question, UserProfile, TestResult
from .serializers import (
    RegisterSerializer, CustomTokenSerializer,
    UserProfileSerializer, TestListSerializer,
    TestDetailSerializer, TestResultSerializer,
)


# ── Главная страница ──────────────────────────────────────────────────────────
def home(request):
    return render(request, 'index.html')


# ── AUTH ──────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — логин, возвращает access + refresh токены"""
    serializer_class = CustomTokenSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ — регистрация нового пользователя"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Сразу выдаём токены, чтобы не нужно было делать второй запрос
        refresh = RefreshToken.for_user(user)
        return Response({
            'message':  'Регистрация успешна!',
            'username': user.username,
            'access':   str(refresh.access_token),
            'refresh':  str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """POST /api/auth/logout/ — инвалидируем refresh токен"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Выход выполнен успешно.'})
    except Exception:
        return Response({'error': 'Неверный токен.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """GET/PATCH /api/auth/profile/ — профиль текущего пользователя"""
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'PATCH':
        for field in ('full_name', 'grade', 'city'):
            if field in request.data:
                setattr(prof, field, request.data[field])
        prof.save()
    serializer = UserProfileSerializer(prof)
    return Response(serializer.data)


# ── ТЕСТЫ ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def subject_list(request):
    """GET /api/subjects/"""
    subjects = [
        {'key': 'chemistry', 'name': 'Химия',       'emoji': '⚗️'},
        {'key': 'biology',   'name': 'Биология',     'emoji': '🧬'},
        {'key': 'math',      'name': 'Математика',   'emoji': '📐'},
        {'key': 'history',   'name': 'История',      'emoji': '📜'},
        {'key': 'russian',   'name': 'Русский язык', 'emoji': '✍️'},
    ]
    for s in subjects:
        s['test_count'] = Test.objects.filter(subject=s['key']).count()
    return Response(subjects)


@api_view(['GET'])
def test_list(request):
    """GET /api/tests/?subject=chemistry"""
    subject = request.query_params.get('subject')
    qs = Test.objects.all()
    if subject:
        qs = qs.filter(subject=subject)
    return Response(TestListSerializer(qs, many=True).data)


@api_view(['GET'])
def test_detail(request, pk):
    """GET /api/tests/<id>/"""
    try:
        test = Test.objects.prefetch_related('questions').get(pk=pk)
    except Test.DoesNotExist:
        return Response({'error': 'Тест не найден'}, status=status.HTTP_404_NOT_FOUND)
    return Response(TestDetailSerializer(test).data)


@api_view(['GET'])
def stats(request):
    """GET /api/stats/"""
    return Response({
        'total_tests':     Test.objects.count(),
        'total_questions': Question.objects.count(),
        'by_subject': {
            s: Test.objects.filter(subject=s).count()
            for s in ['chemistry', 'biology', 'math', 'history', 'russian']
        },
    })


# ── РЕЗУЛЬТАТЫ ────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_result(request):
    """POST /api/results/ — сохранить результат теста"""
    serializer = TestResultSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_results(request):
    """GET /api/results/ — история результатов текущего пользователя"""
    results = TestResult.objects.filter(user=request.user).select_related('test')
    return Response(TestResultSerializer(results, many=True).data)