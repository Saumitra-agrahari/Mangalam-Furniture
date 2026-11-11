from django.http import Http404
from django.views.generic import DetailView, ListView

from core.cache import get_active_categories

from .models import Item


class CategoryIndexView(ListView):
    template_name = "catalog/category_index.html"
    context_object_name = "categories"

    def get_queryset(self):
        return get_active_categories()


class CategoryListView(ListView):
    template_name = "catalog/category_list.html"
    context_object_name = "items"

    def get_queryset(self):
        slug = self.kwargs["category_slug"]
        self.category = next(
            (category for category in get_active_categories() if category.slug == slug),
            None,
        )
        if self.category is None:
            raise Http404("No Category matches the given query.")
        return (
            Item.objects.filter(category=self.category, is_active=True)
            .select_related("category")
            .prefetch_related("images")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ItemDetailView(DetailView):
    template_name = "catalog/item_detail.html"
    context_object_name = "item"
    slug_url_kwarg = "item_slug"

    def get_queryset(self):
        return (
            Item.objects.filter(
                category__slug=self.kwargs["category_slug"],
                category__is_active=True,
                is_active=True,
            )
            .select_related("category")
            .prefetch_related("images")
        )
