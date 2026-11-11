from django.views.generic import TemplateView

from core.cache import get_shop_info


class AboutView(TemplateView):
    template_name = "shop_info/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shop_info"] = get_shop_info()
        return context
