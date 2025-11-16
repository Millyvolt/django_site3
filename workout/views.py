from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Max
import json
from django.utils import timezone

from .models import Exercise, WorkoutSession, WorkoutSet
from .forms import WorkoutSessionForm, WorkoutSetForm


class SessionListView(ListView):
    """List all workout sessions for logged-in user"""
    model = WorkoutSession
    template_name = 'workout/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter sessions by logged-in user"""
        return WorkoutSession.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        """Add active session info for badge on list page"""
        context = super().get_context_data(**kwargs)
        active_session = WorkoutSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()
        context['active_session'] = active_session
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """Require login"""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class SessionDetailView(DetailView):
    """View details of a specific workout session"""
    model = WorkoutSession
    template_name = 'workout/session_detail.html'
    context_object_name = 'session'
    
    def get_queryset(self):
        """Filter sessions by logged-in user"""
        return WorkoutSession.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        """Add grouped sets to context"""
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Group sets by exercise
        sets_by_exercise = {}
        for workout_set in session.workout_sets.all().select_related('exercise'):
            exercise_name = workout_set.exercise.name
            if exercise_name not in sets_by_exercise:
                sets_by_exercise[exercise_name] = []
            sets_by_exercise[exercise_name].append(workout_set)
        
        # Add active session status and elapsed time
        context['sets_by_exercise'] = sets_by_exercise
        context['is_active'] = session.is_active
        
        if session.is_active:
            # Calculate elapsed time in seconds for active sessions
            elapsed = timezone.now() - session.date
            base_offset_seconds = int((session.duration or 0) * 60)
            context['elapsed_time_seconds'] = base_offset_seconds + int(elapsed.total_seconds())
            context['session_start_iso'] = session.date.isoformat()
            context['base_offset_seconds'] = base_offset_seconds
        else:
            # For ended sessions, use calculated duration
            if session.end_time:
                elapsed = session.end_time - session.date
                context['elapsed_time_seconds'] = int(elapsed.total_seconds())
            else:
                # Fallback to duration field if end_time is not set
                context['elapsed_time_seconds'] = (session.duration * 60) if session.duration else 0
        
        context['end_time'] = session.end_time
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """Require login"""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class SessionCreateView(CreateView):
    """Create a new workout session"""
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = 'workout/session_form.html'
    
    def get(self, request, *args, **kwargs):
        """Check if user already has an active session"""
        if request.user.is_authenticated:
            active_session = WorkoutSession.objects.filter(
                user=request.user, 
                is_active=True
            ).first()
            if active_session:
                messages.warning(
                    request, 
                    f'You already have an active workout session. Please end it before starting a new one.'
                )
                return redirect('workout:session_detail', pk=active_session.pk)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Set user to current user and mark session as active"""
        form.instance.user = self.request.user
        form.instance.is_active = True
        # Ensure date is set if not provided
        if not form.instance.date:
            form.instance.date = timezone.now()
        
        # Save the form instance
        self.object = form.save()
        messages.success(self.request, 'Workout session started!')
        
        # Redirect to the session detail page instead of list
        return redirect('workout:session_detail', pk=self.object.pk)
    
    def dispatch(self, request, *args, **kwargs):
        """Require login"""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class SessionUpdateView(UpdateView):
    """Update an existing workout session"""
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = 'workout/session_form.html'
    success_url = reverse_lazy('workout:session_list')
    
    def get_queryset(self):
        """Filter sessions by logged-in user"""
        return WorkoutSession.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Show success message"""
        messages.success(self.request, 'Workout session updated successfully!')
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Require login"""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class SessionDeleteView(DeleteView):
    """Delete a workout session"""
    model = WorkoutSession
    template_name = 'workout/session_confirm_delete.html'
    success_url = reverse_lazy('workout:session_list')
    context_object_name = 'session'
    
    def get_queryset(self):
        """Filter sessions by logged-in user"""
        return WorkoutSession.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Show success message"""
        messages.success(request, 'Workout session deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        """Require login"""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


@login_required
def end_session(request, pk):
    """End an active workout session"""
    session = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    
    if not session.is_active:
        messages.warning(request, 'This session is already ended.')
        return redirect('workout:session_detail', pk=pk)
    
    # End the session
    session.is_active = False
    session.end_time = timezone.now()
    
    # Calculate and accumulate duration (minutes)
    delta = session.end_time - session.date
    newly_elapsed_minutes = int(delta.total_seconds() / 60)
    session.duration = (session.duration or 0) + newly_elapsed_minutes
    
    session.save()
    messages.success(request, f'Workout session ended. Duration: {session.duration} minutes.')
    return redirect('workout:session_detail', pk=pk)

@login_required
def resume_session(request, pk):
    """Resume a previously ended workout session (only if no other active session)."""
    session = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    if session.is_active:
        messages.info(request, 'This session is already active.')
        return redirect('workout:session_detail', pk=pk)
    # Prevent multiple active sessions
    other_active = WorkoutSession.objects.filter(user=request.user, is_active=True).exclude(pk=pk).first()
    if other_active:
        messages.warning(request, 'You already have an active session. Please end it before resuming another one.')
        return redirect('workout:session_detail', pk=other_active.pk)
    # Reactivate: continue timing from now, keep previous accumulated duration
    session.is_active = True
    session.end_time = None
    session.date = timezone.now()
    session.save(update_fields=['is_active', 'end_time', 'date'])
    messages.success(request, 'Session resumed. Timer continues from previous duration.')
    return redirect('workout:session_detail', pk=pk)


@login_required
def set_add(request, session_id):
    """Add sets to a workout session"""
    session = get_object_or_404(WorkoutSession, pk=session_id, user=request.user)
    
    if request.method == 'POST':
        form = WorkoutSetForm(request.POST)
        if form.is_valid():
            workout_set = form.save(commit=False)
            workout_set.workout_session = session
            # If set_number not provided, auto-increment per exercise
            if not workout_set.set_number:
                next_num = session.workout_sets.filter(exercise=workout_set.exercise).aggregate(
                    m=Max('set_number')
                )['m'] or 0
                workout_set.set_number = next_num + 1
            workout_set.save()
            messages.success(request, f'Set #{workout_set.set_number} for {workout_set.exercise.name} added successfully!')
            return redirect('workout:session_detail', pk=session_id)
    else:
        # Compute next set number per exercise within this session
        per_ex_max = session.workout_sets.values('exercise').annotate(m=Max('set_number'))
        next_by_exercise = {str(row['exercise']): (row['m'] or 0) + 1 for row in per_ex_max}
        # Default initial number as next overall for UX fallback
        overall_next = (session.workout_sets.aggregate(m=Max('set_number'))['m'] or 0) + 1
        form = WorkoutSetForm(initial={'set_number': overall_next})
    
    context = {
        'form': form,
        'session': session,
        'exercise_next_map_json': json.dumps(next_by_exercise),
    }
    return render(request, 'workout/set_form.html', context)


class ExerciseListView(ListView):
    """List all available exercises"""
    model = Exercise
    template_name = 'workout/exercise_list.html'
    context_object_name = 'exercises'
    paginate_by = 20
    
    def get_queryset(self):
        """Allow search filtering"""
        queryset = Exercise.objects.all()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(muscle_groups__icontains=search_query) |
                Q(equipment_needed__icontains=search_query)
            )
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        """Add search query to context"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context
