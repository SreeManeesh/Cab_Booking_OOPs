"""
Accounts Models
===============
Database models for user accounts and gaze authentication profiles.
"""

from django.db import models
from django.contrib.auth.models import User
import json


class GazeProfile(models.Model):
    """
    Stores gaze authentication data for a user.
    Contains the enrolled gaze signature and authentication settings.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gaze_profile')

    # Gaze signature data (JSON serialized)
    gaze_signature = models.TextField(blank=True, null=True)

    # Enrollment status
    is_enrolled = models.BooleanField(default=False)
    enrollment_samples = models.IntegerField(default=0)
    enrollment_date = models.DateTimeField(null=True, blank=True)

    # Authentication settings
    auth_threshold = models.FloatField(default=0.7)
    use_gaze_auth = models.BooleanField(default=False)

    # Statistics
    successful_auths = models.IntegerField(default=0)
    failed_auths = models.IntegerField(default=0)
    last_auth_date = models.DateTimeField(null=True, blank=True)

    # Model file paths
    svm_model_path = models.CharField(max_length=255, blank=True, null=True)
    cnn_model_path = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_signature(self, signature_data: dict):
        """Store gaze signature as JSON."""
        self.gaze_signature = json.dumps(signature_data)
        self.save()

    def get_signature(self) -> dict:
        """Retrieve gaze signature from JSON."""
        if self.gaze_signature:
            return json.loads(self.gaze_signature)
        return {}

    def record_auth_attempt(self, success: bool):
        """Record an authentication attempt."""
        from django.utils import timezone
        if success:
            self.successful_auths += 1
        else:
            self.failed_auths += 1
        self.last_auth_date = timezone.now()
        self.save()

    def get_auth_success_rate(self) -> float:
        """Calculate authentication success rate."""
        total = self.successful_auths + self.failed_auths
        if total == 0:
            return 0.0
        return self.successful_auths / total

    def __str__(self):
        status = "Enrolled" if self.is_enrolled else "Not Enrolled"
        return f"{self.user.username} - Gaze Profile ({status})"

    class Meta:
        verbose_name = "Gaze Profile"
        verbose_name_plural = "Gaze Profiles"


class GazeSession(models.Model):
    """
    Records a gaze authentication session for analysis.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gaze_sessions')

    # Session type
    SESSION_TYPES = [
        ('enrollment', 'Enrollment'),
        ('authentication', 'Authentication'),
        ('calibration', 'Calibration'),
    ]
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)

    # Session data (JSON)
    features_data = models.TextField(blank=True, null=True)

    # Results
    success = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # seconds

    # Additional info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)

    def set_features(self, features: dict):
        """Store features as JSON."""
        self.features_data = json.dumps(features)

    def get_features(self) -> dict:
        """Retrieve features from JSON."""
        if self.features_data:
            return json.loads(self.features_data)
        return {}

    def complete_session(self, success: bool, confidence: float = None):
        """Mark session as complete."""
        from django.utils import timezone
        self.success = success
        self.confidence_score = confidence
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.session_type} ({self.started_at})"

    class Meta:
        ordering = ['-started_at']
        verbose_name = "Gaze Session"
        verbose_name_plural = "Gaze Sessions"
