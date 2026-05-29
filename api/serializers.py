from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Test, Question, UserProfile, TestResult


# ── AUTH ──────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True,
                                      validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True,
                                      label='Подтверждение пароля')
    full_name = serializers.CharField(required=False, allow_blank=True)
    grade     = serializers.CharField(required=False, allow_blank=True)
    city      = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password', 'password2',
                  'full_name', 'grade', 'city')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Пароли не совпадают.'})
        if User.objects.filter(email=attrs.get('email', '')).exists():
            raise serializers.ValidationError({'email': 'Email уже используется.'})
        return attrs

    def create(self, validated_data):
        # Убираем лишние поля перед созданием User
        full_name = validated_data.pop('full_name', '')
        grade     = validated_data.pop('grade', '')
        city      = validated_data.pop('city', '')
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            grade=grade,
            city=city,
        )
        return user


class CustomTokenSerializer(TokenObtainPairSerializer):
    """Добавляем имя пользователя в ответ токена"""
    def validate(self, attrs):
        data = super().validate(attrs)
        data['username']  = self.user.username
        data['full_name'] = getattr(self.user, 'profile', None) and \
                            self.user.profile.full_name or ''
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    username     = serializers.CharField(source='user.username', read_only=True)
    email        = serializers.CharField(source='user.email', read_only=True)
    tests_passed = serializers.IntegerField(source='tests_passed', read_only=True)
    avg_score    = serializers.FloatField(source='avg_score', read_only=True)

    class Meta:
        model  = UserProfile
        fields = ('username', 'email', 'full_name', 'grade', 'city',
                  'tests_passed', 'avg_score', 'created_at')


# ── TESTS ─────────────────────────────────────────────────────────────────────

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model  = Question
        fields = ['id', 'text', 'options', 'correct', 'explanation']

    def get_options(self, obj):
        return [obj.option_a, obj.option_b, obj.option_c, obj.option_d]


class TestListSerializer(serializers.ModelSerializer):
    question_count     = serializers.IntegerField(source='questions.count', read_only=True)
    subject_display    = serializers.CharField(source='get_subject_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model  = Test
        fields = ['id', 'name', 'subject', 'subject_display',
                  'difficulty', 'difficulty_display',
                  'time_limit', 'description', 'question_count', 'created_at']


class TestDetailSerializer(TestListSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(TestListSerializer.Meta):
        fields = TestListSerializer.Meta.fields + ['questions']


# ── RESULTS ───────────────────────────────────────────────────────────────────

class TestResultSerializer(serializers.ModelSerializer):
    test_name    = serializers.CharField(source='test.name', read_only=True)
    test_subject = serializers.CharField(source='test.subject', read_only=True)

    class Meta:
        model  = TestResult
        fields = ['id', 'test', 'test_name', 'test_subject',
                  'score', 'correct', 'total', 'created_at']
        read_only_fields = ['created_at']