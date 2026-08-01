import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

if __name__ == '__main__':
    from django.core.management import call_command
    call_command('migrate')

