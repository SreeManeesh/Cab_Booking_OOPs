# Gaze Authentication - Deployment Guide

## Deployment Options

### Option 1: Local Development (Current)
```bash
cd "GazeAuthApp/Website Code"
python manage.py runserver 0.0.0.0:8000
```
Access: http://localhost:8000

---

### Option 2: PythonAnywhere (Free Hosting)

**Recommended for:** Demo/testing, free tier available

1. Create account at https://www.pythonanywhere.com
2. Upload project files via Files tab or Git
3. Create a new Web App (Manual configuration, Python 3.10)
4. Set up virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 gazeauth
   pip install -r requirements.txt
   ```
5. Configure WSGI file to point to your Django app
6. Set ALLOWED_HOSTS in settings.py to include your domain
7. Collect static files: `python manage.py collectstatic`

---

### Option 3: Railway (Easy Deployment)

**Recommended for:** Quick deployment, free tier

1. Create account at https://railway.app
2. Connect your GitHub repository
3. Add environment variables:
   ```
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app
   ```
4. Railway auto-detects Django and deploys

---

### Option 4: Render (Free Tier)

**Recommended for:** Production-ready, free tier

1. Create account at https://render.com
2. Create new Web Service from GitHub repo
3. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn GazeGesture.wsgi:application`
4. Add environment variables
5. Add `gunicorn` to requirements.txt

---

### Option 5: Heroku

1. Install Heroku CLI
2. Create Procfile:
   ```
   web: gunicorn GazeGesture.wsgi:application
   ```
3. Add to requirements.txt:
   ```
   gunicorn
   whitenoise
   ```
4. Deploy:
   ```bash
   heroku login
   heroku create gaze-auth-app
   git push heroku master
   ```

---

### Option 6: AWS EC2 / DigitalOcean Droplet

**For production with full control:**

1. Create Ubuntu 22.04 server
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```
3. Clone repository and set up venv
4. Configure Gunicorn as systemd service
5. Configure Nginx as reverse proxy
6. Set up SSL with Let's Encrypt

---

## Production Checklist

### settings.py Changes for Production

```python
# SECURITY
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Required Files for Deployment

1. **requirements.txt** - Already exists
2. **Procfile** (for Heroku/Railway):
   ```
   web: gunicorn GazeGesture.wsgi:application
   ```
3. **runtime.txt** (optional):
   ```
   python-3.10.x
   ```

### Environment Variables

```bash
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
DATABASE_URL=<if using external database>
ALLOWED_HOSTS=your-domain.com
```

### Generate New Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## Database Options

### SQLite (Current - Development Only)
- Simple, file-based
- Not recommended for production with multiple users

### PostgreSQL (Recommended for Production)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gazeauth',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## Static Files for Production

1. Add whitenoise to requirements.txt:
   ```
   whitenoise
   ```

2. Add to MIDDLEWARE (after SecurityMiddleware):
   ```python
   'whitenoise.middleware.WhiteNoiseMiddleware',
   ```

3. Configure static files:
   ```python
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

4. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

---

## HTTPS/SSL Requirements

Gaze authentication requires camera access, which browsers only allow over HTTPS (except localhost).

**Options:**
- Use a hosting platform that provides SSL (Railway, Render, Heroku)
- Set up Let's Encrypt with Certbot
- Use Cloudflare for SSL termination

---

## Quick Deploy to Railway (Recommended)

1. Push code to GitHub
2. Go to https://railway.app
3. Click "New Project" > "Deploy from GitHub repo"
4. Select your repository
5. Add environment variable: `SECRET_KEY=<your-key>`
6. Railway will auto-deploy

Your app will be live at: `https://your-app.railway.app`
