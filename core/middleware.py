from django.conf import settings
from django.utils.cache import add_never_cache_headers

PUBLIC_CACHEABLE_URL_NAMES = frozenset(
    {
        "core:home",
        "catalog:category-index",
        "catalog:category-list",
        "catalog:item-detail",
        "shop_info:about",
    }
)


class PublicCacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        match = getattr(request, "resolver_match", None)
        view_name = match.view_name if match else None

        is_safe = request.method in ("GET", "HEAD")
        is_allowlisted = view_name in PUBLIC_CACHEABLE_URL_NAMES
        has_user_or_cookie = (
            settings.SESSION_COOKIE_NAME in request.COOKIES
            or bool(response.cookies)
            or "Cookie" in response.get("Vary", "")
        )

        if is_safe and response.status_code == 200 and is_allowlisted and not has_user_or_cookie:
            if not response.has_header("Cache-Control"):
                response["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
        elif not response.has_header("Cache-Control"):
            add_never_cache_headers(response)

        return response
