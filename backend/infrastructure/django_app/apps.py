from django.apps import AppConfig


class DjangoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.django_app'

    def ready(self) -> None:
        """Import signals to register them when the app is ready."""
        import infrastructure.django_app.signals  # noqa: F401
