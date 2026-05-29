"""
Converter Views
===============
Main application views including homepage and gaze tracking interface.
"""

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import sys
import os

# cv2 is optional - only needed for server-side video streaming (not used in production)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Add gaze_auth to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def welcome(request):
    """Public landing page for non-authenticated users."""
    return render(request, 'welcome_pwa.html')


def landing(request):
    """Smart landing - shows welcome or redirects to home based on auth status."""
    if request.user.is_authenticated:
        return redirect('/home/')
    return render(request, 'welcome_pwa.html')


@login_required
def homepage(request):
    """Main homepage for authenticated users."""
    from accounts.models import GazeProfile

    context = {
        'user': request.user,
    }

    # Check if user has gaze profile
    try:
        gaze_profile = request.user.gaze_profile
        context['gaze_profile'] = gaze_profile
        context['is_enrolled'] = gaze_profile.is_enrolled

        # Stats for homepage
        context['stats'] = {
            'successful_auths': gaze_profile.successful_auths,
            'failed_auths': gaze_profile.failed_auths,
        }
    except GazeProfile.DoesNotExist:
        gaze_profile = GazeProfile.objects.create(user=request.user)
        context['gaze_profile'] = gaze_profile
        context['is_enrolled'] = False
        context['stats'] = {'successful_auths': 0, 'failed_auths': 0}

    return render(request, 'homepage_pwa.html', context)


@login_required
def dashboard(request):
    """User dashboard with gaze authentication statistics."""
    from accounts.models import GazeProfile, GazeSession

    context = {
        'user': request.user,
    }

    try:
        gaze_profile = request.user.gaze_profile
        context['gaze_profile'] = gaze_profile

        # Get recent sessions
        recent_sessions = GazeSession.objects.filter(
            user=request.user
        ).order_by('-started_at')[:5]
        context['recent_sessions'] = recent_sessions

        # Calculate statistics
        context['stats'] = {
            'total_auths': gaze_profile.successful_auths + gaze_profile.failed_auths,
            'success_rate': gaze_profile.get_auth_success_rate() * 100,
            'is_enrolled': gaze_profile.is_enrolled,
        }
    except GazeProfile.DoesNotExist:
        gaze_profile = GazeProfile.objects.create(user=request.user)
        context['gaze_profile'] = gaze_profile
        context['recent_sessions'] = []
        context['stats'] = {
            'total_auths': 0,
            'success_rate': 0,
            'is_enrolled': False,
        }

    return render(request, 'dashboard_pwa.html', context)


@login_required
def gaze_tracker_view(request):
    """Live gaze tracker interface."""
    return render(request, 'gaze_tracker_pwa.html', {
        'user': request.user
    })


def generate_frames():
    """Generator function for streaming video frames with gaze tracking."""
    if not CV2_AVAILABLE:
        return
    try:
        from gaze_auth import GazeTracker
        from gaze_auth.utils import draw_gaze_overlay

        tracker = GazeTracker(use_mediapipe=True)
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame with gaze tracker
            result = tracker.process_frame(frame)

            # Draw overlay
            annotated = draw_gaze_overlay(
                frame,
                result,
                show_landmarks=True,
                show_gaze_point=True,
                show_info=True
            )

            # Encode frame
            ret, buffer = cv2.imencode('.jpg', annotated)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cap.release()
        tracker.release()

    except ImportError:
        # Fallback without gaze tracking
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Add simple text
            cv2.putText(frame, "Gaze Auth Module Not Available",
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cap.release()


@login_required
def video_feed(request):
    """Video streaming endpoint."""
    if not CV2_AVAILABLE:
        return JsonResponse({'error': 'Video streaming not available on this server'}, status=503)
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


@csrf_exempt
def process_gaze_frame(request):
    """Process a single frame for gaze tracking (AJAX endpoint)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    if not CV2_AVAILABLE:
        return JsonResponse({'error': 'Server-side gaze processing not available. Use client-side MediaPipe.'}, status=503)

    try:
        import base64
        import numpy as np

        # Get frame data from request
        data = request.POST.get('frame')
        if not data:
            return JsonResponse({'error': 'No frame data'}, status=400)

        # Decode base64 image
        img_data = base64.b64decode(data.split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Process with gaze tracker
        try:
            from gaze_auth import GazeTracker
            from gaze_auth.blink_detector import BlinkDetector
            from gaze_auth.feature_extractor import FeatureExtractor

            # Initialize tracker (in production, cache this)
            tracker = GazeTracker(use_mediapipe=True)
            blink_detector = BlinkDetector()
            feature_extractor = FeatureExtractor()

            # Process frame
            result = tracker.process_frame(frame)

            response = {
                'success': True,
                'face_detected': result.get('face_detected', False),
                'gaze_ratio': result.get('gaze_ratio'),
                'vertical_ratio': result.get('vertical_ratio'),
            }

            # Process blink if eyes detected
            if result.get('left_eye') is not None and result.get('right_eye') is not None:
                blink_result = blink_detector.detect_blink(
                    result['left_eye'],
                    result['right_eye'],
                    result['timestamp']
                )
                response['blink_detected'] = blink_result['blink_detected']
                response['ear_average'] = blink_result['ear_average']
                response['blink_rate'] = blink_result['blink_rate']

            # Process gaze features
            if result.get('gaze_point') is not None and result.get('left_pupil') is not None:
                feature_result = feature_extractor.process_gaze_data(
                    result['gaze_point'],
                    result['left_pupil'],
                    result['timestamp']
                )
                if feature_result.get('fixation'):
                    response['fixation'] = feature_result['fixation']
                if feature_result.get('saccade'):
                    response['saccade'] = feature_result['saccade']

            tracker.release()
            return JsonResponse(response)

        except ImportError as e:
            return JsonResponse({
                'success': False,
                'error': f'Gaze module not available: {str(e)}'
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
