"""
WSGI config for GazeGesture project.
Root-level wrapper for Render deployment.
"""
import os
import sys

# Add the Django project directory to the path
PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'GazeAuthApp',
                           'Website Code')
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GazeGesture.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
