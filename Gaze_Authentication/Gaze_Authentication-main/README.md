# Gaze Authentication System

A biometric authentication system using eye movement tracking that prevents unauthorized access from shoulder surfers. This Progressive Web Application (PWA) uses real-time gaze detection with MediaPipe for secure, password-less authentication.

## Features

- **Gaze-Based Authentication** - Users authenticate using their unique eye movement patterns and physical eye characteristics (IPD, EAR)
- **Real-Time Eye Tracking** - Detects and processes gaze direction using MediaPipe Face Mesh with iris tracking
- **Progressive Web App (PWA)** - Installable on mobile devices with offline support
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices
- **9-Point Calibration System** - Improves tracking accuracy with personalized calibration
- **Multi-Sample Enrollment** - 5-sample enrollment process for reliable authentication
- **Prevention of Shoulder Surfing** - No visible passwords or PINs for attackers to observe

## Tech Stack

### Backend
- **Django 4.2** - Web framework
- **SQLite/PostgreSQL** - Database (SQLite for local, PostgreSQL for production)
- **Python 3.10+** - Programming language

### Computer Vision & ML
- **MediaPipe** - Real-time facial landmark detection with iris tracking
- **OpenCV** - Computer vision and image processing
- **scikit-learn** - SVM-based authentication model
- **NumPy/SciPy** - Numerical computing and signal processing

### Frontend
- **Tailwind CSS** - Utility-first CSS framework with glass morphism design
- **Font Awesome** - Icons
- **MediaPipe Face Mesh JS** - Client-side eye tracking
- **Service Worker** - Offline support and caching

## Project Structure

```
GazeAuthentication/
├── GazeAuthApp/                        # Main application
│   ├── Website Code/                   # Django web application
│   │   ├── GazeGesture/               # Django project settings
│   │   │   ├── settings.py            # Configuration
│   │   │   ├── urls.py                # URL routing
│   │   │   └── wsgi.py                # WSGI config
│   │   ├── accounts/                   # User authentication app
│   │   │   ├── models.py              # GazeProfile, GazeSession models
│   │   │   └── views.py               # Auth & gaze views
│   │   ├── converter/                  # Main application views
│   │   ├── templates/                  # PWA HTML templates
│   │   │   ├── base_pwa.html          # Base template with Tailwind
│   │   │   ├── login_pwa.html         # Login page
│   │   │   ├── register_pwa.html      # Registration page
│   │   │   ├── homepage_pwa.html      # Homepage
│   │   │   ├── dashboard_pwa.html     # User dashboard
│   │   │   ├── gaze_enrollment_pwa.html    # 5-sample enrollment
│   │   │   ├── gaze_auth_pwa.html     # Gaze verification
│   │   │   ├── gaze_calibration_pwa.html   # 9-point calibration
│   │   │   ├── gaze_tracker_pwa.html  # Real-time gaze test
│   │   │   └── gaze_settings_pwa.html # Settings page
│   │   └── static/                     # Static files
│   │       ├── manifest.json          # PWA manifest
│   │       ├── sw.js                  # Service worker
│   │       └── js/gaze_processor.js   # Client-side gaze processing
│   └── Trial Code/                     # Research and experimental code
│
├── Screenshots/                        # Application screenshots
├── docs/                               # Documentation
│   ├── USER_GUIDE.md                  # User manual
│   └── DEPLOYMENT.md                  # Deployment options
├── manage.py                           # Django management script
├── requirements.txt                    # Python dependencies
├── Procfile                            # Production deployment config
├── render.yaml                         # Render deployment config
└── README.md                           # This file
```

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Webcam for gaze tracking
- Modern browser (Chrome recommended)

### Quick Setup (Local Development)

1. **Extract the project**
   ```bash
   tar -xzvf GazeAuthentication.tar.gz
   cd GazeAuthentication
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   Open http://localhost:8000 in your browser

## Usage Guide

### Registration
1. Navigate to the application
2. Click "Register" and fill in your details
3. You'll be redirected to login

### Gaze Enrollment
1. Login to your account
2. Navigate to "Enroll Gaze" from the homepage
3. Allow camera access when prompted
4. Complete 5 enrollment samples (5 seconds each)
5. Your unique gaze signature is now stored

### Authentication
1. Enable gaze authentication in Settings
2. On next login, after password verification, you'll be prompted for gaze verification
3. Look at the camera naturally for 3 seconds
4. If your gaze pattern matches, you're authenticated

### Calibration (Optional)
1. Navigate to "Calibrate" for improved accuracy
2. Follow the 9-point calibration targets
3. Look at each target as it appears

## Key Algorithms

### Eye Aspect Ratio (EAR)
Used for blink detection:
```
EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
```
Where p1-p6 are eye landmark points. EAR drops below 0.25 during a blink.

### Inter-Pupillary Distance (IPD)
Physical measurement of skull structure - unique to each individual.

### I-DT Fixation Detection
Dispersion-threshold algorithm:
- If gaze dispersion < 0.02 for > 100ms, it's a fixation

### Velocity-based Saccade Detection
- Gaze velocity > 300 pixels/second indicates a saccade

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register/` | GET, POST | User registration |
| `/login/` | GET, POST | User login |
| `/logout/` | GET | User logout |
| `/` | GET | Homepage |
| `/dashboard/` | GET | User dashboard |
| `/gaze-enrollment/` | GET | Enrollment page |
| `/api/gaze-enrollment/` | POST | Submit enrollment sample |
| `/gaze-auth/` | GET | Gaze authentication page |
| `/api/gaze-auth/` | POST | Verify gaze pattern |
| `/gaze-calibration/` | GET | Calibration page |
| `/settings/` | GET, POST | User settings |

## Database

### Local Development
Uses SQLite database (`db.sqlite3`) - automatically created on first migration.

### Production
Supports PostgreSQL via `DATABASE_URL` environment variable.

## Screenshots

The application features a modern, responsive UI with:
- Glass morphism design
- Gradient buttons and cards
- Mobile-friendly bottom navigation
- Real-time gaze visualization

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please contact the development team.
