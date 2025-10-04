from django.contrib import admin

from .models import Choice, Question, UserCodeSubmission, UserProfile


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]

class UserCodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_id', 'language', 'code_preview', 'updated_at']
    list_filter = ['language', 'updated_at', 'created_at']
    search_fields = ['user__username', 'question_id', 'code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_image', 'has_custom_image', 'updated_at']
    list_filter = ['default_image', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

admin.site.register(Question, QuestionAdmin)
admin.site.register(UserCodeSubmission, UserCodeSubmissionAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
