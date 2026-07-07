import os
import django
try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()
    print("Django setup successful!")
except Exception as e:
    print(f"Exception during django setup: {e}")
