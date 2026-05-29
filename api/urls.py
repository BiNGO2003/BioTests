from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Фронтенд
    path('', views.home, name='home'),

    # Auth
    path('api/auth/register/', views.register,       name='register'),
    path('api/auth/login/',    views.LoginView.as_view(), name='login'),
    path('api/auth/logout/',   views.logout,          name='logout'),
    path('api/auth/refresh/',  TokenRefreshView.as_view(), name='token-refresh'),
    path('api/auth/profile/',  views.profile,         name='profile'),

    # Тесты
    path('api/subjects/',       views.subject_list,  name='subject-list'),
    path('api/tests/',          views.test_list,     name='test-list'),
    path('api/tests/<int:pk>/', views.test_detail,   name='test-detail'),
    path('api/stats/',          views.stats,         name='stats'),

    # Результаты
    path('api/results/',        views.save_result,   name='save-result'),
    path('api/results/my/',     views.my_results,    name='my-results'),
]