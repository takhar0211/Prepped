import os
import django
try:
    import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()
    print("Django setup successful!")
except Exception as e:
    print(f"Exception during django setup: {e}")
