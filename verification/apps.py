from django.apps import AppConfig


class VerificationConfig(AppConfig):
    name = 'verification'

    def ready(self):
        import verification.signals
