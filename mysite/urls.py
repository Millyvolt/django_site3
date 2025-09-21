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
from django.urls import include, path
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("leetcode-home/", views.leetcode_home, name="leetcode_home"),
    path("daily-question/", views.daily_question, name="daily_question"),
    path("test-html/", views.test_html, name="test_html"),
    path("leetcode/", views.leetcode, name="leetcode"),
    path("editor/", views.question_editor, name="question_editor"),
    path("editor/<str:question_id>/", views.question_editor, name="question_editor_with_id"),
    path("compile/", views.compile_code, name="compile_code"),
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
] + debug_toolbar_urls()

if not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()
