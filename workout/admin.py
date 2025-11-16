from django.contrib import admin
from .models import Exercise, WorkoutSession, WorkoutSet


class WorkoutSetInline(admin.TabularInline):
    """Inline for WorkoutSet in WorkoutSession admin"""
    model = WorkoutSet
    extra = 1
    fields = ['exercise', 'set_number', 'reps', 'weight', 'rest_time', 'notes']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_groups', 'equipment_needed', 'created_at']
    search_fields = ['name', 'muscle_groups']
    list_filter = ['created_at']


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
