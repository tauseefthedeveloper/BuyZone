from django.apps import AppConfig


class BuyoneappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'buyzoneapp'

    def ready(self):
        import buyzoneapp.signals