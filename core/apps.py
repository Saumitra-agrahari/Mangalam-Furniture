from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "core"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from catalog.models import Category
        from core.cache import invalidate_categories_cache, invalidate_shop_info_cache
        from shop_info.models import ShopInfo

        post_save.connect(
            invalidate_categories_cache,
            sender=Category,
            dispatch_uid="core_invalidate_categories_save",
        )
        post_delete.connect(
            invalidate_categories_cache,
            sender=Category,
            dispatch_uid="core_invalidate_categories_delete",
        )
        post_save.connect(
            invalidate_shop_info_cache,
            sender=ShopInfo,
            dispatch_uid="core_invalidate_shop_info_save",
        )
        post_delete.connect(
            invalidate_shop_info_cache,
            sender=ShopInfo,
            dispatch_uid="core_invalidate_shop_info_delete",
        )
