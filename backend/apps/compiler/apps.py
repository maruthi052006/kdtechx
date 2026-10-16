from django.apps import AppConfig


class CompilerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.compiler'
    verbose_name = 'Online Compiler & Code Execution Engine'
