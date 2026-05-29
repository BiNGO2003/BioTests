from django.contrib import admin
from django.utils.html import format_html
from .models import Test, Question, UserProfile, TestResult


# ── UserProfile ───────────────────────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'full_name', 'grade', 'city', 'tests_passed_count', 'created_at')
    search_fields = ('user__username', 'full_name', 'city')
    ordering      = ('-created_at',)

    def tests_passed_count(self, obj):
        count = obj.user.results.count()
        return format_html('<b style="color:#3ecf8e">{}</b>', count)
    tests_passed_count.short_description = 'Тестов пройдено'


# ── TestResult ────────────────────────────────────────────────────────────────
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display  = ('user', 'test', 'score_badge', 'correct', 'total', 'created_at')
    list_filter   = ('test__subject',)
    search_fields = ('user__username', 'test__name')
    ordering      = ('-created_at',)

    def score_badge(self, obj):
        color = '#3ecf8e' if obj.score >= 80 else '#f5a623' if obj.score >= 60 else '#f26c6c'
        return format_html('<b style="color:{}">{:.0f}%</b>', color, obj.score)
    score_badge.short_description = 'Результат'


# ── Test ──────────────────────────────────────────────────────────────────────
class QuestionInline(admin.TabularInline):
    model   = Question
    extra   = 3
    fields  = ('text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct', 'explanation')
    classes = ['collapse']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display  = ('name', 'colored_subject', 'difficulty_badge', 'question_count', 'time_limit', 'created_at')
    list_filter   = ('subject', 'difficulty')
    search_fields = ('name',)
    inlines       = [QuestionInline]

    def question_count(self, obj):
        n = obj.questions.count()
        color = '#3ecf8e' if n > 0 else '#f26c6c'
        return format_html('<b style="color:{}">{}</b>', color, n)
    question_count.short_description = 'Вопросов'

    def colored_subject(self, obj):
        colors = {'chemistry':'#7c6ff7','biology':'#3ecf8e','math':'#f5a623','history':'#f26c6c','russian':'#60b8f7'}
        emoji  = {'chemistry':'⚗️','biology':'🧬','math':'📐','history':'📜','russian':'✍️'}
        return format_html('<span style="color:{};font-weight:600">{} {}</span>',
                           colors.get(obj.subject,'#888'), emoji.get(obj.subject,''), obj.get_subject_display())
    colored_subject.short_description = 'Предмет'

    def difficulty_badge(self, obj):
        s = {'easy':('🟢','#3ecf8e'),'medium':('🟡','#f5a623'),'hard':('🔴','#f26c6c')}
        icon, color = s.get(obj.difficulty, ('⚪','#888'))
        return format_html('<span style="color:{}">{} {}</span>', color, icon, obj.get_difficulty_display())
    difficulty_badge.short_description = 'Сложность'


# ── Question ──────────────────────────────────────────────────────────────────
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ('short_text', 'test', 'correct', 'created_at')
    list_filter   = ('test__subject', 'test')
    search_fields = ('text',)

    def short_text(self, obj):
        return obj.text[:75] + '…' if len(obj.text) > 75 else obj.text
    short_text.short_description = 'Вопрос'


admin.site.site_header = '⚗️ ExamPrep — Панель администратора'
admin.site.site_title  = 'ExamPrep Admin'
admin.site.index_title = 'Управление платформой'