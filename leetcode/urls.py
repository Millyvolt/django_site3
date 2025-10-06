from django.urls import path
from . import views

app_name = 'leetcode'

urlpatterns = [
    path('leetcode-home/', views.home, name='home'),
    path('pick-question/', views.question_selection, name='question_selection'),
    path('editor/', views.question_editor, name='question_editor'),
    path('editor/<str:question_id>/', views.question_editor, name='question_editor_with_id'),
    path('daily-question/', views.daily_question, name='daily_question'),
    path('compile/', views.compile_code, name='compile_code'),
    path('fetch-cpp-template/', views.fetch_cpp_template, name='fetch_cpp_template'),
]


