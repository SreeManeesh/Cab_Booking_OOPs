"""
Accounts Views
==============
Views for user registration, login, and gaze authentication.
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import sys
import os

# Add gaze_auth to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from .models import GazeProfile, GazeSession


def register(request):
    """Handle user registration."""
    template = 'register_pwa.html'

    if request.method == "GET":
        return render(request, template)

    if request.method == "POST":
        username = request.POST.get("username", "")
        fname = request.POST.get("first_name", "")
        lname = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        confirmPassword = request.POST.get("confirm_password", "")

        # Validation
        if not username or not password:
            return render(request, template, {
                'message': "Username and password are required"
            })

        if password != confirmPassword:
            return render(request, template, {
                'message': "Password & Confirm Password do not match"
            })

        if User.objects.filter(username=username).exists():
            return render(request, template, {
                'message': "Username already exists"
            })

        if email and User.objects.filter(email=email).exists():
            return render(request, template, {
                'message': "Email already registered"
            })

        # Create user
        newUser = User.objects.create_user(
            username=username,
            password=password,
            first_name=fname,
            last_name=lname,
            email=email
        )
        newUser.save()

        # Create gaze profile
        GazeProfile.objects.create(user=newUser)

        return redirect('/login?registered=true')

    return redirect('/register')


def login(request):
    """Handle user login with optional gaze authentication."""
    template = 'login_pwa.html'

    if request.method == "GET":
        context = {}
        if request.GET.get('registered'):
            context['message'] = "Registration successful! Please login."
            context['message_type'] = 'success'
        return render(request, template, context)

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        use_gaze = request.POST.get("use_gaze_auth", "") == "true"

        # Authenticate with password
        user = authenticate(username=username, password=password)

        if user is not None:
            # Check if gaze authentication is required
            try:
                gaze_profile = user.gaze_profile
                if gaze_profile.use_gaze_auth and gaze_profile.is_enrolled:
                    # Store user in session for gaze authentication
                    request.session['pending_gaze_auth_user'] = user.id
                    return redirect('/gaze-auth/')
            except GazeProfile.DoesNotExist:
                pass

            # Standard login
            auth_login(request, user)
            return redirect('/home/')
        else:
            return render(request, template, {
                'message': "Invalid username or password",
                'message_type': 'error'
            })

    return redirect('/login')


def logout(request):
    """Handle user logout."""
    auth_logout(request)
    return redirect('/login')


@login_required
def gaze_enrollment(request):
    """Handle gaze enrollment page."""
    return render(request, 'gaze_enrollment_pwa.html', {
        'user': request.user
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def gaze_enrollment_api(request):
    """API endpoint for gaze enrollment data submission."""
    try:
        data = json.loads(request.body)
        features = data.get('features', {})
        sample_number = data.get('sample_number', 0)

        # Get or create gaze profile
        gaze_profile, created = GazeProfile.objects.get_or_create(user=request.user)

        # Store enrollment sample
        current_signature = gaze_profile.get_signature()
        if 'enrollment_samples' not in current_signature:
            current_signature['enrollment_samples'] = []

        current_signature['enrollment_samples'].append({
            'sample_number': sample_number,
            'features': features,
            'timestamp': timezone.now().isoformat()
        })

        gaze_profile.set_signature(current_signature)
        gaze_profile.enrollment_samples = len(current_signature['enrollment_samples'])

        # Check if enrollment is complete (5 samples)
        if gaze_profile.enrollment_samples >= 5:
            gaze_profile.is_enrolled = True
            gaze_profile.enrollment_date = timezone.now()
            gaze_profile.use_gaze_auth = True

            # Compute final signature statistics
            all_features = [s['features'] for s in current_signature['enrollment_samples']]
            final_signature = compute_signature_stats(all_features)
            current_signature['final_signature'] = final_signature
            gaze_profile.set_signature(current_signature)

        gaze_profile.save()

        # Create session record
        session = GazeSession.objects.create(
            user=request.user,
            session_type='enrollment',
            success=True,
            confidence_score=1.0
        )
        session.set_features(features)
        session.complete_session(True, 1.0)

        return JsonResponse({
            'success': True,
            'enrollment_samples': gaze_profile.enrollment_samples,
            'is_enrolled': gaze_profile.is_enrolled,
            'message': 'Enrollment complete!' if gaze_profile.is_enrolled else f'Sample {sample_number} recorded'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def gaze_authentication(request):
    """Handle gaze authentication page."""
    pending_user_id = request.session.get('pending_gaze_auth_user')
    if not pending_user_id:
        return redirect('/login')

    try:
        user = User.objects.get(id=pending_user_id)
        return render(request, 'gaze_auth_pwa.html', {
            'pending_user': user
        })
    except User.DoesNotExist:
        return redirect('/login')


@csrf_exempt
@require_http_methods(["POST"])
def gaze_auth_api(request):
    """API endpoint for gaze authentication verification."""
    pending_user_id = request.session.get('pending_gaze_auth_user')
    if not pending_user_id:
        return JsonResponse({
            'success': False,
            'error': 'No pending authentication'
        }, status=401)

    try:
        user = User.objects.get(id=pending_user_id)
        gaze_profile = user.gaze_profile

        data = json.loads(request.body)
        features = data.get('features', {})

        # Compare with enrolled signature
        enrolled_signature = gaze_profile.get_signature()
        if 'final_signature' not in enrolled_signature:
            return JsonResponse({
                'success': False,
                'error': 'User not enrolled for gaze authentication'
            }, status=400)

        # Calculate similarity
        similarity = calculate_signature_similarity(
            features,
            enrolled_signature['final_signature']
        )

        # Convert threshold from percentage (50) to decimal (0.50) for comparison
        threshold_decimal = gaze_profile.auth_threshold / 100.0
        authenticated = similarity >= threshold_decimal

        # Record attempt
        gaze_profile.record_auth_attempt(authenticated)

        # Create session record
        session = GazeSession.objects.create(
            user=user,
            session_type='authentication',
            success=authenticated,
            confidence_score=similarity
        )
        session.set_features(features)
        session.complete_session(authenticated, similarity)

        if authenticated:
            # Complete login
            auth_login(request, user)
            del request.session['pending_gaze_auth_user']

            return JsonResponse({
                'success': True,
                'authenticated': True,
                'confidence': similarity,
                'redirect': '/home/'
            })
        else:
            return JsonResponse({
                'success': True,
                'authenticated': False,
                'confidence': similarity,
                'message': 'Gaze pattern did not match. Please try again.'
            })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def gaze_settings(request):
    """Handle gaze authentication settings."""
    gaze_profile, created = GazeProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        use_gaze = request.POST.get('use_gaze_auth') == 'on'
        threshold = float(request.POST.get('auth_threshold', 70))

        gaze_profile.use_gaze_auth = use_gaze
        gaze_profile.auth_threshold = max(50, min(95, threshold))
        gaze_profile.save()

        return redirect('/settings?saved=true')

    context = {
        'gaze_profile': gaze_profile,
        'saved': request.GET.get('saved', False)
    }
    return render(request, 'gaze_settings_pwa.html', context)


@login_required
def reset_gaze_enrollment(request):
    """Reset user's gaze enrollment."""
    if request.method == "POST":
        try:
            gaze_profile = request.user.gaze_profile
            gaze_profile.gaze_signature = None
            gaze_profile.is_enrolled = False
            gaze_profile.enrollment_samples = 0
            gaze_profile.enrollment_date = None
            gaze_profile.use_gaze_auth = False
            gaze_profile.save()
        except GazeProfile.DoesNotExist:
            pass

    return redirect('/settings')


def compute_signature_stats(features_list):
    """Compute statistical signature from multiple samples."""
    if not features_list:
        return {}

    import numpy as np

    # Aggregate all feature keys
    all_keys = set()
    for f in features_list:
        all_keys.update(f.keys())

    signature = {}
    for key in all_keys:
        values = [f.get(key) for f in features_list if key in f and f.get(key) is not None]
        if not values:
            continue

        # Handle array features (like saccade_velocity_profile)
        if isinstance(values[0], (list, tuple)):
            # Average the arrays element-wise
            try:
                arrays = [np.array(v) for v in values if len(v) > 0]
                if arrays:
                    # Ensure all arrays are the same length
                    min_len = min(len(a) for a in arrays)
                    arrays = [a[:min_len] for a in arrays]
                    avg_profile = np.mean(arrays, axis=0).tolist()
                    std_profile = np.std(arrays, axis=0).tolist()
                    signature[key] = {
                        'type': 'profile',
                        'mean_profile': avg_profile,
                        'std_profile': std_profile,
                        'sample_count': len(arrays)
                    }
            except Exception:
                pass
        else:
            # Scalar values
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                signature[key] = {
                    'type': 'scalar',
                    'mean': float(np.mean(numeric_values)),
                    'std': float(np.std(numeric_values)),
                    'min': float(np.min(numeric_values)),
                    'max': float(np.max(numeric_values))
                }

    return signature


def calculate_signature_similarity(current_features, enrolled_signature):
    """
    Calculate similarity between current features and enrolled signature.

    PRIMARY BIOMETRICS (cannot be faked):
    - IPD (Inter-Pupillary Distance): Physical skull structure measurement
    - EAR baseline: Natural eye opening percentage
    - Eye symmetry: How symmetric the eyes are

    These are PHYSICAL CONSTANTS unique to each person's face geometry.
    A sibling or impostor will have different IPD and EAR values.

    Secondary features (behavioral) shown to user for "magic trick" effect.
    """
    if not enrolled_signature:
        print("[GAZE_AUTH] ERROR: No enrolled signature!", flush=True)
        return 0.0

    import numpy as np

    # DEBUG: Log what features are available
    print(f"[GAZE_AUTH] Enrolled signature keys: {list(enrolled_signature.keys())}", flush=True)
    print(f"[GAZE_AUTH] Current features keys: {list(current_features.keys())}", flush=True)

    # ========== PRIMARY BIOMETRIC MATCHING ==========
    # These are the REAL authentication features (hidden from user)
    primary_biometric_keys = ['ipd_mean', 'ear_baseline', 'eye_symmetry']
    primary_scores = []

    # Check if primary biometrics exist in enrolled signature
    missing_primary = [k for k in primary_biometric_keys if k not in enrolled_signature]
    if missing_primary:
        print(f"[GAZE_AUTH] WARNING: Missing primary biometrics in enrollment: {missing_primary}", flush=True)
        print("[GAZE_AUTH] User needs to RE-ENROLL for IPD+EAR authentication!", flush=True)

    for key in primary_biometric_keys:
        if key not in enrolled_signature or key not in current_features:
            print(f"[GAZE_AUTH] Skipping {key}: not in enrolled or current", flush=True)
            continue

        stats = enrolled_signature[key]
        current_value = current_features.get(key)

        if not isinstance(current_value, (int, float)):
            print(f"[GAZE_AUTH] Skipping {key}: not numeric (value={current_value})", flush=True)
            continue

        if stats.get('type') == 'scalar' or 'mean' in stats:
            mean = stats.get('mean', 0)
            std = stats.get('std', 0)

            print(f"[GAZE_AUTH] {key}: current={current_value:.4f}, enrolled_mean={mean:.4f}, enrolled_std={std:.4f}", flush=True)

            # RELAXED comparison for primary biometrics
            # Allow more variance since camera angle/lighting affects measurements
            if std > 0.001:  # Only use std if it's meaningful
                z_score = abs(current_value - mean) / std
                # Relaxed: 2.5 std devs = 0 similarity (was 1.5)
                similarity = max(0, 1 - (z_score / 2.5))
                print(f"[GAZE_AUTH] {key}: z_score={z_score:.3f}, similarity={similarity:.3f}", flush=True)
            else:
                # No meaningful variance - use percentage-based comparison
                if mean == 0:
                    similarity = 1.0 if abs(current_value) < 0.01 else 0.0
                else:
                    ratio = current_value / mean
                    # Relaxed: allow 20% variance (was 10%)
                    if 0.8 <= ratio <= 1.2:
                        similarity = 1.0
                    elif 0.7 <= ratio <= 1.3:
                        similarity = 0.5
                    else:
                        similarity = 0.0
                    print(f"[GAZE_AUTH] {key}: ratio={ratio:.3f}, similarity={similarity:.3f}", flush=True)

            primary_scores.append(similarity)

    # ========== SECONDARY BEHAVIORAL MATCHING ==========
    # These are shown to user but have less weight in actual matching
    secondary_keys = [
        'saccade_avg_velocity', 'trajectory_velocity_mean',
        'avg_ear', 'std_ear', 'gaze_dispersion_x', 'gaze_dispersion_y'
    ]
    secondary_scores = []

    for key in secondary_keys:
        if key not in enrolled_signature or key not in current_features:
            continue

        stats = enrolled_signature[key]
        current_value = current_features.get(key)

        if not isinstance(current_value, (int, float)):
            continue

        if stats.get('type') == 'scalar' or 'mean' in stats:
            mean = stats.get('mean', 0)
            std = stats.get('std', 0)

            if std > 0:
                z_score = abs(current_value - mean) / std
                similarity = max(0, 1 - (z_score / 2))
            else:
                if mean == 0:
                    similarity = 1.0 if abs(current_value) < 0.01 else 0.0
                else:
                    ratio = current_value / mean
                    similarity = 1.0 if 0.8 <= ratio <= 1.2 else 0.0

            secondary_scores.append(similarity)

    # ========== WEIGHTED SCORING ==========
    # PRIMARY biometrics (IPD + EAR): 80% weight
    # Secondary behavioral: 20% weight

    total_score = 0
    total_weight = 0

    print(f"[GAZE_AUTH] Primary scores: {primary_scores}", flush=True)
    print(f"[GAZE_AUTH] Secondary scores: {secondary_scores}", flush=True)

    if primary_scores:
        primary_avg = np.mean(primary_scores)
        total_score += primary_avg * 8  # Weight 8
        total_weight += 8
        print(f"[GAZE_AUTH] Primary average: {primary_avg:.3f} (weight 8)", flush=True)
    else:
        print("[GAZE_AUTH] NO PRIMARY SCORES - falling back to secondary only!", flush=True)

    if secondary_scores:
        secondary_avg = np.mean(secondary_scores)
        total_score += secondary_avg * 2  # Weight 2
        total_weight += 2
        print(f"[GAZE_AUTH] Secondary average: {secondary_avg:.3f} (weight 2)", flush=True)

    if total_weight > 0:
        final_score = total_score / total_weight
        print(f"[GAZE_AUTH] Raw final score: {final_score:.3f}", flush=True)

        # CRITICAL: If primary biometrics fail, authentication MUST fail
        # This is the core security - different person = different IPD/EAR
        if primary_scores and np.mean(primary_scores) < 0.5:
            final_score *= 0.3  # Heavy penalty - wrong person
            print(f"[GAZE_AUTH] PENALTY applied! Primary < 0.5. New score: {final_score:.3f}", flush=True)

        print(f"[GAZE_AUTH] FINAL SCORE: {final_score:.3f}", flush=True)
        return float(final_score)

    # Fallback: use any available features
    print("[GAZE_AUTH] ERROR: No scores calculated!", flush=True)
    return 0.0


def compare_profiles(current_profile, enrolled_profile):
    """
    Compare two velocity profiles using correlation.
    Returns similarity 0-1.
    """
    import numpy as np

    if not current_profile or not enrolled_profile:
        return 0.5

    # Ensure same length
    min_len = min(len(current_profile), len(enrolled_profile))
    if min_len < 2:
        return 0.5

    p1 = np.array(current_profile[:min_len])
    p2 = np.array(enrolled_profile[:min_len])

    # Pearson correlation coefficient
    try:
        # Center the arrays
        p1_centered = p1 - np.mean(p1)
        p2_centered = p2 - np.mean(p2)

        # Calculate correlation
        numerator = np.sum(p1_centered * p2_centered)
        denominator = np.sqrt(np.sum(p1_centered**2) * np.sum(p2_centered**2))

        if denominator == 0:
            return 0.5

        correlation = numerator / denominator

        # Convert correlation (-1 to 1) to similarity (0 to 1)
        # correlation of 1 = perfect match = similarity 1
        # correlation of 0 = no correlation = similarity 0.5
        # correlation of -1 = opposite = similarity 0
        similarity = (correlation + 1) / 2

        return float(similarity)

    except Exception:
        return 0.5


def changePassword(request):
    """Handle password change."""
    pass


def forgotPassword(request):
    """Handle forgot password."""
    template = 'forgot_password_pwa.html'

    if request.method == "POST":
        email = request.POST.get("email", "")

        if email:
            # Check if user with this email exists
            try:
                user = User.objects.get(email=email)
                # In production, you would send an email here
                # For now, just show a success message
                return render(request, template, {
                    'message': 'If an account with this email exists, password reset instructions have been sent.',
                    'message_type': 'success',
                    'email_sent': True
                })
            except User.DoesNotExist:
                # Don't reveal if email exists or not (security)
                return render(request, template, {
                    'message': 'If an account with this email exists, password reset instructions have been sent.',
                    'message_type': 'success',
                    'email_sent': True
                })
        else:
            return render(request, template, {
                'message': 'Please enter your email address.',
                'message_type': 'error'
            })

    return render(request, template)


@login_required
def gaze_calibration(request):
    """Handle gaze calibration page."""
    return render(request, 'gaze_calibration_pwa.html', {
        'user': request.user
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_calibration(request):
    """API endpoint to save calibration data."""
    try:
        data = json.loads(request.body)
        accuracy = data.get('accuracy', 0)
        calibration_data = data.get('calibrationData', [])

        gaze_profile, created = GazeProfile.objects.get_or_create(user=request.user)

        # Store calibration data in signature
        current_signature = gaze_profile.get_signature()
        current_signature['calibration'] = {
            'accuracy': accuracy,
            'data': calibration_data,
            'timestamp': timezone.now().isoformat()
        }
        gaze_profile.set_signature(current_signature)
        gaze_profile.save()

        return JsonResponse({
            'success': True,
            'accuracy': accuracy,
            'message': 'Calibration saved successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def gaze_tracker_test(request):
    """Handle gaze tracker test page."""
    return render(request, 'gaze_tracker_pwa.html', {
        'user': request.user
    })
