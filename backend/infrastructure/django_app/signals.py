"""
Django signals for automatic model creation.

Signals are connected in apps.py via the ready() method.
"""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from infrastructure.django_app.models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[User], instance: User, created: bool, **kwargs: object
) -> None:
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance, role="customer")
