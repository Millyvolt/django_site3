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
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("collab/", include("collab.urls")),
    path("leetcode/", include(("leetcode.urls", "leetcode"), namespace="leetcode")),
    # Legacy root endpoints redirect to new /leetcode/ paths
    path("leetcode-home/", RedirectView.as_view(url="/leetcode/leetcode-home/", permanent=False), name="leetcode_home"),
    path("pick-question/", RedirectView.as_view(url="/leetcode/pick-question/", permanent=False)),
    path("editor/", RedirectView.as_view(url="/leetcode/editor/", permanent=False)),
    path("editor/<str:question_id>/", RedirectView.as_view(url="/leetcode/editor/", permanent=False)),
    path("daily-question/", RedirectView.as_view(url="/leetcode/daily-question/", permanent=False)),
    path("test-html/", views.test_html, name="test_html"),
    path("test-network/", views.test_network_connectivity, name="test_network"),
    path("test-functionality/", views.test_site_functionality, name="test_functionality"),
    path("test-buttons/", views.test_button_functionality, name="test_buttons"),
    # Legacy endpoints removed; app namespace owns these routes
    
    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("accounts/password_reset/", auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name="password_reset"),
    path("accounts/password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name="password_reset_confirm"),
    path("accounts/reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name="password_reset_complete"),
    
    # Code saving URL
    path("save-code/", views.save_user_code, name="save_user_code"),
    
    # Test URL for debugging
    path("test-static/", views.test_static_files, name="test_static_files"),
    
    # Media file serving
    path("media/<path:path>", views.serve_media, name="serve_media"),
    
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
]

# Add debug toolbar URLs only when not in testing mode
if not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()

# Serve media and static files during development
if settings.DEBUG:
    # Note: Media files are now served by the custom serve_media view above
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files - use WhiteNoise for ASGI servers like Uvicorn
    from django.contrib.staticfiles.views import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve),
    ]
