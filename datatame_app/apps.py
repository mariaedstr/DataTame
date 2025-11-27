from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datatame_app'

class DatatameAppConfig(AppConfig):
    name = 'datatame_app'

    def ready(self):
        import datatame_app.signals