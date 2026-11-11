from core.cache import get_active_categories, get_shop_info


def site_context(request):
    return {
        "site_name": "Manglam Furniture",
        "nav_categories": get_active_categories(),
        "shop_info": get_shop_info(),
    }
