from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recommendations"
    verbose_name = "Gợi ý món ăn"

    def ready(self):
        import recommendations.signals  # noqa: F401
