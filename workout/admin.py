from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Exercise, WorkoutSession, WorkoutSet


class WorkoutSetInline(admin.TabularInline):
    """Inline for WorkoutSet in WorkoutSession admin"""
    model = WorkoutSet
    extra = 1
    fields = ['exercise', 'set_number', 'reps', 'weight', 'rest_time', 'notes']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_groups', 'equipment_needed', 'image_thumb', 'created_at']
    search_fields = ['name', 'muscle_groups']
    list_filter = ['created_at']
    fields = ['name', 'description', 'muscle_groups', 'equipment_needed', 'image', 'image_thumb']
    readonly_fields = ['image_thumb']
    
    def image_thumb(self, obj):
        if getattr(obj, 'image', None):
            try:
                return mark_safe(f'<img src="{obj.image.url}" style="height:60px;" />')
            except Exception:
                return "—"
        return "—"
    image_thumb.short_description = "Preview"


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_exercises', 'total_sets', 'duration']
    list_filter = ['date', 'user']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WorkoutSetInline]
    fieldsets = [
        (None, {'fields': ['user', 'date']}),
        ('Workout Details', {'fields': ['duration', 'notes']}),
        ('Timestamps', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ['workout_session', 'exercise', 'set_number', 'reps', 'weight', 'rest_time']
    list_filter = ['exercise', 'workout_session__date']
    search_fields = ['exercise__name', 'workout_session__user__username']
