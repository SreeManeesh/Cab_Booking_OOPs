"""
GazeGesture URL Configuration
=============================
URL routing for the Gaze Authentication web application.
"""

from django.contrib import admin
from django.urls import path
from accounts.views import (
    login, register, logout, forgotPassword,
    gaze_enrollment, gaze_enrollment_api,
    gaze_authentication, gaze_auth_api,
    gaze_settings, reset_gaze_enrollment,
    gaze_calibration, save_calibration, gaze_tracker_test
)
from converter.views import homepage, dashboard, gaze_tracker_view, landing, welcome

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Public pages
    path('', landing, name='landing'),
    path('welcome/', welcome, name='welcome'),

    # Authentication
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('forgot-password/', forgotPassword, name='forgot_password'),

    # Gaze Authentication
    path('gaze-enrollment/', gaze_enrollment, name='gaze_enrollment'),
    path('api/gaze-enrollment/', gaze_enrollment_api, name='gaze_enrollment_api'),
    path('gaze-auth/', gaze_authentication, name='gaze_auth'),
    path('api/gaze-auth/', gaze_auth_api, name='gaze_auth_api'),

    # Settings
    path('settings/', gaze_settings, name='gaze_settings'),
    path('reset-gaze/', reset_gaze_enrollment, name='reset_gaze'),
    path('reset-gaze-enrollment/', reset_gaze_enrollment, name='reset_gaze_enrollment'),

    # Calibration
    path('gaze-calibration/', gaze_calibration, name='gaze_calibration'),
    path('api/save-calibration/', save_calibration, name='save_calibration'),

    # Main pages (authenticated)
    path('home/', homepage, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('gaze-tracker/', gaze_tracker_test, name='gaze_tracker'),
]
