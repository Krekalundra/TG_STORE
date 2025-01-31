from django.apps import AppConfig

class TgshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tgshop'
    verbose_name = "Магазин"

    def ready(self):
        import tgshop.models.categories
        import tgshop.models.operators
        import tgshop.models.product
        import tgshop.models.productImage
        import tgshop.models.settings
        import tgshop.models.customer
        import tgshop.models.order
        import tgshop.models.cart
        
