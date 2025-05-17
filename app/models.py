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
    
    ANGRY = 'angry'
    NOSTALGIC = 'nostalgic'
    IRONIC = 'ironic'
    FUNNY = 'funny'
    POETIC = 'poetic'
    RELIEVED = 'relieved'
    
    TONE_CHOICES = [
        (ANGRY, 'Angry'),
        (NOSTALGIC, 'Nostalgic'),
        (IRONIC, 'Ironic'),
        (FUNNY, 'Funny'),
        (POETIC, 'Poetic'),
        (RELIEVED, 'Relieved')
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
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default=NOSTALGIC)
    
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

