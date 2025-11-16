from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Exercise(models.Model):
    """Exercise catalog - stores exercise definitions"""
    name = models.CharField(max_length=200, help_text="Exercise name (e.g., 'Bench Press')")
    description = models.TextField(blank=True, null=True, help_text="Exercise description")
    muscle_groups = models.CharField(max_length=200, blank=True, null=True, help_text="Target muscle groups")
    equipment_needed = models.CharField(max_length=200, blank=True, null=True, help_text="Required equipment")
    image = models.ImageField(upload_to='exercises/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class WorkoutSession(models.Model):
    """Represents a single workout session on a specific date/time"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    date = models.DateTimeField(help_text="Workout date and time")
    duration = models.IntegerField(blank=True, null=True, help_text="Workout duration in minutes")
    notes = models.TextField(blank=True, null=True, help_text="Session notes")
    is_active = models.BooleanField(default=False, help_text="Whether this session is currently active")
    end_time = models.DateTimeField(blank=True, null=True, help_text="When the session ended")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        status = " (Active)" if self.is_active else ""
        return f"{self.user.username} - {self.date.strftime('%Y-%m-%d %H:%M')}{status}"
    
    @property
    def total_exercises(self):
        """Count of unique exercises in this workout session"""
        return self.workout_sets.values('exercise').distinct().count()
    
    @property
    def total_sets(self):
        """Total count of sets in this workout session"""
        return self.workout_sets.count()
    
    def calculate_duration(self):
        """Calculate duration in minutes from start to end time"""
        end = self.end_time if self.end_time else timezone.now()
        if self.date and end:
            delta = end - self.date
            return int(delta.total_seconds() / 60)
        return None


class WorkoutSet(models.Model):
    """Links exercises to workout sessions with set/reps/weight data"""
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='workout_sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='workout_sets')
    set_number = models.IntegerField(help_text="Set number (1, 2, 3, etc.)")
    reps = models.IntegerField(blank=True, null=True, help_text="Number of repetitions")
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight in lbs/kg")
    rest_time = models.IntegerField(blank=True, null=True, help_text="Rest time in seconds")
    notes = models.CharField(max_length=200, blank=True, null=True, help_text="Set-specific notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['set_number']
        unique_together = ['workout_session', 'exercise', 'set_number']
    
    def __str__(self):
        return f"{self.exercise.name} - Set #{self.set_number}"
