from django.db import models
from django.contrib.auth.models import User

# ── Справочники ───────────────────────────────────────────────────────────────
SUBJECT_CHOICES = [
    ('chemistry', 'Химия'),
    ('biology',   'Биология'),
    ('math',      'Математика'),
    ('history',   'История'),
    ('russian',   'Русский язык'),
]
DIFFICULTY_CHOICES = [
    ('easy',   'Лёгкий'),
    ('medium', 'Средний'),
    ('hard',   'Сложный'),
]


# ── Профиль пользователя ──────────────────────────────────────────────────────
class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE,
                                      related_name='profile', verbose_name='Пользователь')
    full_name  = models.CharField(max_length=150, blank=True, verbose_name='Полное имя')
    grade      = models.CharField(max_length=10, blank=True, verbose_name='Класс',
                                  help_text='Например: 11')
    city       = models.CharField(max_length=100, blank=True, verbose_name='Город')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Профиль'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль: {self.user.username}'

    def tests_passed(self):
        return self.user.results.count()

    def avg_score(self):
        results = self.user.results.all()
        if not results:
            return 0
        return round(sum(r.score for r in results) / len(results), 1)


# ── Тест ──────────────────────────────────────────────────────────────────────
class Test(models.Model):
    name        = models.CharField(max_length=200, verbose_name='Название')
    subject     = models.CharField(max_length=20, choices=SUBJECT_CHOICES, verbose_name='Предмет')
    difficulty  = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES,
                                   default='easy', verbose_name='Сложность')
    time_limit  = models.PositiveIntegerField(default=10, verbose_name='Время (мин)')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.get_subject_display()} — {self.name}'


# ── Вопрос ────────────────────────────────────────────────────────────────────
class Question(models.Model):
    test        = models.ForeignKey(Test, on_delete=models.CASCADE,
                                    related_name='questions', verbose_name='Тест')
    text        = models.TextField(verbose_name='Текст вопроса')
    option_a    = models.CharField(max_length=400, verbose_name='Вариант A')
    option_b    = models.CharField(max_length=400, verbose_name='Вариант B')
    option_c    = models.CharField(max_length=400, verbose_name='Вариант C')
    option_d    = models.CharField(max_length=400, verbose_name='Вариант D')
    correct     = models.PositiveSmallIntegerField(
                    choices=[(0,'A'),(1,'B'),(2,'C'),(3,'D')],
                    verbose_name='Правильный ответ')
    explanation = models.TextField(blank=True, verbose_name='Объяснение')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering            = ['created_at']

    def __str__(self):
        return self.text[:80]


# ── Результат прохождения теста ───────────────────────────────────────────────
class TestResult(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='results', verbose_name='Пользователь')
    test       = models.ForeignKey(Test, on_delete=models.CASCADE,
                                   related_name='results', verbose_name='Тест')
    score      = models.FloatField(verbose_name='Результат (%)')
    correct    = models.PositiveIntegerField(verbose_name='Правильных ответов')
    total      = models.PositiveIntegerField(verbose_name='Всего вопросов')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Результат'
        verbose_name_plural = 'Результаты тестов'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.test.name} — {self.score}%'