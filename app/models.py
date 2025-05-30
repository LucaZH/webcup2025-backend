from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 

    def __str__(self):
        return self.email if self.email else self.username  


class DeparturePage(models.Model):
    BREAKUP = 'breakup'
    WORK = 'work'
    PROJECT = 'project'
    COMMUNITY = 'community'
    OTHER = 'other'

    ENDING_TYPE_CHOICES = [
        (BREAKUP, 'Romantic Breakup'),
        (WORK, 'Work Resignation/Burnout'),
        (PROJECT, 'Project Ending'),
        (COMMUNITY, 'Community Departure'),
        (OTHER, 'Other')
    ]

    LIBERATING_JOY = 'liberating_joy'
    SADNESS = 'sadness'
    DISGUST = 'disgust'
    EXPLOSIVE_ANGER = 'explosive_anger'
    DETACHED_IRONY = 'detached_irony'
    HILARIOUS = 'hilarious'
    POETIC = 'poetic'
    EXISTENTIAL_VOID = 'existential_void'
    ACCEPTANCE = 'acceptance'
    CONFUSED = 'confused'

    EMOTIONAL_TONE_CHOICES = [
        (LIBERATING_JOY, 'Liberating Joy'),
        (SADNESS, 'Sadness'),
        (DISGUST, 'Disgust'),
        (EXPLOSIVE_ANGER, 'Explosive Anger'),
        (DETACHED_IRONY, 'Detached Irony'),
        (HILARIOUS, 'Hilarious'),
        (POETIC, 'Poetic'),
        (EXISTENTIAL_VOID, 'Existential Void'),
        (ACCEPTANCE, 'Acceptance'),
        (CONFUSED, 'Confused')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='departure_pages')
    title = models.CharField(max_length=255)
    content = models.TextField()
    design_data = models.JSONField(default=dict)
    template_id = models.CharField(max_length=100)
    creation_date = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    is_ephemeral = models.BooleanField(default=True)
    ending_type = models.CharField(max_length=20, choices=ENDING_TYPE_CHOICES, default=OTHER)
    tone = models.CharField(max_length=25, choices=EMOTIONAL_TONE_CHOICES, default=SADNESS)
    votes_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='departure_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.title}"


class EphemeralReading(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure_page = models.ForeignKey(DeparturePage, on_delete=models.CASCADE, related_name='readings')
    viewer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='viewed_pages')
    has_been_viewed = models.BooleanField(default=False)
    view_date = models.DateTimeField(null=True, blank=True)
    viewer_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['departure_page', 'viewer']


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure_page = models.ForeignKey(DeparturePage, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['departure_page', 'user']
    
    def save(self, *args, **kwargs):
        is_new_vote = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new_vote:
            self.departure_page.votes_count += 1
            self.departure_page.save(update_fields=['votes_count'])
    
    def delete(self, *args, **kwargs):
        self.departure_page.votes_count -= 1
        self.departure_page.save(update_fields=['votes_count'])
        
        super().delete(*args, **kwargs)