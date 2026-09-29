import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates or updates a superuser from environment variables if provided.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD not set. Skipping superuser initialization.")
            return

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}' with ADMIN role."))
        else:
            updated = False
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                updated = True
            if hasattr(user, 'role') and user.role != 'ADMIN':
                user.role = 'ADMIN'
                updated = True
            if updated:
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Updated existing user '{username}' with superuser and ADMIN privileges."))
            else:
                self.stdout.write(f"Superuser '{username}' already configured properly.")
