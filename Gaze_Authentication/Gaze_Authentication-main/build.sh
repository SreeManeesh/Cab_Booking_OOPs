#!/usr/bin/env bash
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files (uses root manage.py which sets correct paths)
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
