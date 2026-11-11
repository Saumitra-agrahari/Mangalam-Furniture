from django.core.cache import cache

from catalog.models import Category
from shop_info.models import ShopInfo

_MISSING = object()
CACHE_TTL_SECONDS = 120
CATEGORIES_CACHE_KEY = "manglam:active_categories"
SHOP_INFO_CACHE_KEY = "manglam:shop_info"


def get_active_categories():
    cached = cache.get(CATEGORIES_CACHE_KEY, _MISSING)
    if cached is not _MISSING:
        return cached
    categories = list(Category.objects.filter(is_active=True))
    cache.set(CATEGORIES_CACHE_KEY, categories, CACHE_TTL_SECONDS)
    return categories


def get_shop_info():
    cached = cache.get(SHOP_INFO_CACHE_KEY, _MISSING)
    if cached is not _MISSING:
        return cached
    shop_info = ShopInfo.objects.first()
    cache.set(SHOP_INFO_CACHE_KEY, shop_info, CACHE_TTL_SECONDS)
    return shop_info


def invalidate_categories_cache(**kwargs):
    cache.delete(CATEGORIES_CACHE_KEY)


def invalidate_shop_info_cache(**kwargs):
    cache.delete(SHOP_INFO_CACHE_KEY)
