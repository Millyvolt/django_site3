"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.conf import settings
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("leetcode-home/", views.leetcode_home, name="leetcode_home"),
    path("daily-question/", views.daily_question, name="daily_question"),
    path("test-html/", views.test_html, name="test_html"),
    path("pick-question/", views.question_selection, name="question_selection"),
    path("editor/", views.question_editor, name="question_editor"),
    path("editor/<str:question_id>/", views.question_editor, name="question_editor_with_id"),
    path("compile/", views.compile_code, name="compile_code"),
    path("fetch-cpp-template/", views.fetch_cpp_template, name="fetch_cpp_template"),
    
    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/profile/", views.profile_view, name="profile"),
    
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
]

# Add debug toolbar URLs only when not in testing mode
if not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
