# Generated manually for WorkoutSession status fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutsession',
            name='is_active',
            field=models.BooleanField(default=False, help_text='Whether this session is currently active'),
        ),
        migrations.AddField(
            model_name='workoutsession',
            name='end_time',
            field=models.DateTimeField(blank=True, help_text='When the session ended', null=True),
        ),
    ]

