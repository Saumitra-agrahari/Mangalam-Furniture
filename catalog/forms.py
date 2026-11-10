from django import forms
from django.core.exceptions import ValidationError

from .models import Category, ItemImage


MAX_IMAGE_SIZE = 4 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_upload(upload):
    if upload and upload.size > MAX_IMAGE_SIZE:
        raise ValidationError("Images must be 4 MB or smaller.")
    if upload and getattr(upload, "content_type", None) not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    class Media:
        js = ("catalog/js/image-preview.js",)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        validate_image_upload(image)
        return image


class ItemImageAdminForm(forms.ModelForm):
    class Meta:
        model = ItemImage
        fields = "__all__"

    class Media:
        js = ("catalog/js/image-preview.js",)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        validate_image_upload(image)
        return image