"""
Accounts Admin
==============
Django admin configuration for accounts and gaze profiles.
"""

from django.contrib import admin
from .models import GazeProfile, GazeSession


@admin.register(GazeProfile)
class GazeProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'is_enrolled', 'use_gaze_auth',
        'enrollment_samples', 'successful_auths',
        'failed_auths', 'last_auth_date'
    ]
    list_filter = ['is_enrolled', 'use_gaze_auth']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'created_at', 'updated_at', 'enrollment_date',
        'successful_auths', 'failed_auths', 'last_auth_date'
    ]

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Enrollment Status', {
            'fields': (
                'is_enrolled', 'enrollment_samples',
                'enrollment_date', 'gaze_signature'
            )
        }),
        ('Authentication Settings', {
            'fields': ('use_gaze_auth', 'auth_threshold')
        }),
        ('Statistics', {
            'fields': (
                'successful_auths', 'failed_auths',
                'last_auth_date'
            )
        }),
        ('Model Paths', {
            'fields': ('svm_model_path', 'cnn_model_path'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GazeSession)
class GazeSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_type', 'success',
        'confidence_score', 'duration', 'started_at'
    ]
    list_filter = ['session_type', 'success', 'started_at']
    search_fields = ['user__username']
    readonly_fields = [
        'started_at', 'completed_at', 'duration',
        'features_data', 'ip_address', 'user_agent'
    ]

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_type')
        }),
        ('Results', {
            'fields': ('success', 'confidence_score')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Data', {
            'fields': ('features_data',),
            'classes': ('collapse',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
