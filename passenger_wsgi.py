import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set the Django settings module for your project
os.environ['DJANGO_SETTINGS_MODULE'] = 'theendpage.settings'

from theendpage.wsgi import application
