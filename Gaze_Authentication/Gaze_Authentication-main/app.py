"""
Entry point for Railway/Render deployment.
This file makes Railpack detect and run the Django application.
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

# Import and run Django via gunicorn
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
