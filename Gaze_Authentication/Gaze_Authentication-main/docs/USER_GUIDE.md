# Gaze Authentication - User Guide

## Overview

Gaze Authentication is a biometric security system that uses your unique eye movement patterns to verify your identity. This prevents "shoulder surfing" attacks where someone watches you enter a password.

---

## Application Sections

### 1. Login Page (`/login/`)
**Purpose:** Sign in to your account

**Features:**
- Enter username and password
- "Remember me" checkbox to stay logged in
- Link to create a new account
- After password verification, if gaze auth is enabled, you'll be asked for gaze verification

---

### 2. Registration Page (`/register/`)
**Purpose:** Create a new account

**Fields:**
- Username (required)
- First Name
- Last Name
- Email
- Password (required)
- Confirm Password

---

### 3. Homepage (`/`)
**Purpose:** Main dashboard after login

**Sections:**
- **Welcome Banner:** Personalized greeting with "Get Started" button
- **Status Cards:**
  - Enrollment: Shows if you've enrolled your gaze profile (Pending/Complete)
  - Samples: Number of gaze samples collected (0/5 to 5/5)
  - Successful: Count of successful gaze authentications
  - Failed: Count of failed gaze authentications
- **Setup Alert:** Reminder to enroll if not yet done
- **Quick Actions:** Buttons to Calibrate, Enroll, Test, or go to Dashboard
- **How It Works:** Explains the 4-step process

---

### 4. Dashboard (`/dashboard/`)
**Purpose:** Detailed statistics and profile management

**Sections:**
- **Stats Grid:**
  - Total Authentications
  - Success Rate (%)
  - Enrollment Status
  - Gaze Auth Protection (On/Off)
- **Quick Actions:** Same as homepage
- **Recent Sessions:** Last 5 authentication attempts with timestamps
- **Gaze Profile:** Enrollment date, samples, threshold, last auth
- **Security Status:** Shows account, gaze profile, and 2FA status

---

### 5. Gaze Enrollment (`/gaze-enrollment/`)
**Purpose:** Train the system to recognize YOUR unique gaze pattern

**How It Works:**
1. Allow camera access when prompted
2. Position your face in the camera frame
3. Click "Start Enrollment"
4. Look naturally at the screen for ~5 seconds
5. Repeat 5 times (5 samples total)
6. Your unique gaze signature is saved

**What's Captured:**
- Blink patterns (how often and how you blink)
- Fixations (where your eyes rest)
- Saccades (how your eyes move between points)
- Pupil trajectory (movement patterns)

**Live Stats Panel:**
- Face Detected: Yes/No
- Blinks: Count of detected blinks
- Fixations: Count of gaze fixations
- Saccades: Count of rapid eye movements

---

### 6. Gaze Calibration (`/gaze-calibration/`)
**Purpose:** Improve tracking accuracy by calibrating to YOUR eyes

**How It Works:**
1. Allow camera access
2. 9 target points appear one by one on screen
3. Look directly at each target as it appears
4. Keep your head still, only move your eyes
5. System calculates your calibration accuracy

**Best Practices:**
- Good lighting (not too bright, not too dark)
- Consistent distance from screen (~50-70cm)
- Minimize head movement

---

### 7. Gaze Tracker Test (`/gaze-tracker/`)
**Purpose:** Test real-time eye tracking without saving data

**What You See:**
- Live camera feed with face mesh overlay
- EAR (Eye Aspect Ratio) bars for left/right eyes
- Direction Grid showing where you're looking (9 directions)
- Real-time stats: Face detection, blinks, fixations, saccades

**Use This To:**
- Verify your camera is working
- Check lighting conditions
- Practice before enrollment
- Test tracking accuracy

---

### 8. Settings (`/settings/`)
**Purpose:** Configure gaze authentication preferences

**Options:**

#### Gaze Authentication Toggle
- **ON:** After password login, you'll need to verify with your gaze
- **OFF:** Only password required for login
- Note: Cannot enable until you complete enrollment

#### Authentication Threshold (50% - 95%)
- **Lower (50-60%):** Easier to authenticate, less secure
- **Higher (80-95%):** Harder to authenticate, more secure
- **Recommended:** 70-75% for balance of security and convenience

#### Enrollment Status
- Shows: Status, Samples, Enrollment Date, Last Auth
- **Re-enroll:** Record new gaze samples (replaces old ones)
- **Reset Enrollment:** Delete all gaze data and start fresh

#### Authentication Stats
- Total attempts, successful, failed, success rate

---

## How Gaze Authentication Works

### Step 1: Eye Detection
Using MediaPipe Face Mesh, the system detects your face and locates 468 facial landmarks, including detailed eye and iris positions.

### Step 2: Feature Extraction
The system extracts:
- **EAR (Eye Aspect Ratio):** Measures eye openness to detect blinks
- **Fixations:** When your gaze stays in one spot for >100ms
- **Saccades:** Rapid eye movements between fixation points (>300 pixels/sec)
- **Pupil Trajectory:** The path your pupils take

### Step 3: Signature Generation
Your unique features are combined into a "gaze signature" - a mathematical representation of your eye behavior that's unique to you.

### Step 4: Authentication
When you log in with gaze auth enabled:
1. Enter password (verified first)
2. Camera captures your gaze for ~3 seconds
3. System extracts features from current gaze
4. Compares to your enrolled signature
5. If similarity >= threshold, you're authenticated

---

## Troubleshooting

### "Camera not found" error
- Ensure your webcam is connected and working
- Allow camera permissions in browser when prompted
- Try a different browser (Chrome recommended)

### Gaze authentication keeps failing
- Re-calibrate in similar lighting conditions
- Lower the authentication threshold in Settings
- Re-enroll with 5 new samples
- Ensure consistent distance from screen

### Can't log in after enabling gaze auth
- Contact admin to reset your gaze profile, OR
- Use the database reset command (for admins)

### Face not detected
- Improve lighting (avoid backlighting)
- Face the camera directly
- Remove glasses if they cause glare
- Move closer to the camera

---

## Security Benefits

1. **No visible passwords:** Nothing for shoulder surfers to observe
2. **Biometric uniqueness:** Your gaze pattern is unique to you
3. **Two-factor security:** Password + gaze verification
4. **Continuous learning:** System can improve with more samples

---

## Quick Reference

| Action | URL | Purpose |
|--------|-----|---------|
| Login | `/login/` | Sign in |
| Register | `/register/` | Create account |
| Home | `/` | Main dashboard |
| Dashboard | `/dashboard/` | Stats & profile |
| Enroll | `/gaze-enrollment/` | Train gaze pattern |
| Calibrate | `/gaze-calibration/` | Improve accuracy |
| Test | `/gaze-tracker/` | Test eye tracking |
| Settings | `/settings/` | Configure options |
| Logout | `/logout/` | Sign out |

---

## Recommended Setup Flow

1. **Register** a new account
2. **Login** with your credentials
3. **Calibrate** first for better accuracy
4. **Test** the tracker to verify camera works
5. **Enroll** your gaze pattern (5 samples)
6. **Enable** gaze auth in Settings
7. **Logout** and test the full authentication flow
