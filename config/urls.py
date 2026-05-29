from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),       # Django Admin — для добавления тестов
    path('api/',   include('api.urls')),   # REST API
    path('',       include('api.urls')),   # фронтенд на /
]
