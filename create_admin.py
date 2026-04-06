import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from accounts.models import CustomUser

# Create the superuser if it doesn't already exist
username = "admin"
email = "admin@charlady.co.ke"
password = "AdminPassword2026!"

if not CustomUser.objects.filter(username=username).exists():
    CustomUser.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    print(f"Superuser '{username}' created successfully!")
else:
    print(f"Superuser '{username}' already exists. Skipping creation.")
