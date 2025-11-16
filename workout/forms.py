from django import forms
from django.utils import timezone
from .models import Exercise, WorkoutSession, WorkoutSet


class WorkoutSessionForm(forms.ModelForm):
    """Form for creating/editing workout sessions"""
    
    class Meta:
        model = WorkoutSession
        fields = ['date', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Session notes'}),
        }
        labels = {
            'date': 'Workout Date & Time',
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-populate date field with current datetime if creating new session
        if not self.instance.pk:
            # Format current datetime for datetime-local input
            now = timezone.now()
            # Convert to local time and format as YYYY-MM-DDTHH:MM
            local_time = timezone.localtime(now)
            default_value = local_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['date'].widget.attrs['value'] = default_value


class WorkoutSetForm(forms.ModelForm):
    """Form for adding sets to a workout session"""
    
    class Meta:
        model = WorkoutSet
        fields = ['exercise', 'set_number', 'reps', 'weight', 'rest_time', 'notes']
        widgets = {
            'exercise': forms.Select(attrs={'class': 'form-control'}),
            'set_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Reps', 'min': 0}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight (lbs/kg)', 'step': '0.01', 'min': 0}),
            'rest_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rest time (seconds)', 'min': 0}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Set notes', 'maxlength': 200}),
        }
        labels = {
            'exercise': 'Exercise',
            'set_number': 'Set Number',
            'reps': 'Reps',
            'weight': 'Weight',
            'rest_time': 'Rest Time (seconds)',
            'notes': 'Notes',
        }


class WorkoutSetFormSet(forms.BaseFormSet):
    """FormSet for adding multiple sets at once"""
    pass


