
import datetime

from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
from django.templatetags.static import static
import os


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    def __str__(self):
        return self.question_text
    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text


class UserCodeSubmission(models.Model):
    """Model to store user's code submissions for each question"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_id = models.CharField(max_length=100, help_text="LeetCode question ID or identifier")
    code = models.TextField(help_text="User's code submission")
    language = models.CharField(max_length=50, default='cpp', help_text="Programming language used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure one record per user per question
        unique_together = ['user', 'question_id']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - Question {self.question_id} ({self.language})"
    
    @admin.display(
        description="Code Preview",
        ordering="code"
    )
    def code_preview(self):
        """Show first 50 characters of code"""
        return self.code[:50] + "..." if len(self.code) > 50 else self.code


def user_profile_image_path(instance, filename):
    """Generate upload path for user profile images"""
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.user.id}_{instance.user.username}.{ext}"
    return os.path.join('profile_images', filename)


class UserProfile(models.Model):
    """Extended user profile with image functionality"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        null=True,
        blank=True,
        help_text="Upload a custom profile image"
    )
    default_image = models.CharField(
        max_length=50,
        blank=True,
        help_text="Selected default profile image"
    )
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Default profile images available
    DEFAULT_IMAGES = [
        ('avatar1', 'Avatar 1'),
        ('avatar2', 'Avatar 2'),
        ('avatar3', 'Avatar 3'),
        ('avatar4', 'Avatar 4'),
        ('avatar5', 'Avatar 5'),
        ('avatar6', 'Avatar 6'),
    ]
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def get_profile_image_url(self):
        """Return the URL of the profile image (custom or default)"""
        if self.profile_image:
            return self.profile_image.url
        elif self.default_image:
            return static(f"images/default_avatars/{self.default_image}.svg")
        else:
            return static("images/default_avatars/avatar1.svg")
    
    @property
    def has_custom_image(self):
        """Check if user has uploaded a custom image"""
        return bool(self.profile_image)
