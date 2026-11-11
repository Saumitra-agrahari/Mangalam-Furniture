from io import BytesIO
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Category, ItemImage


MAX_IMAGE_SIZE = 4 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1600
IMAGE_QUALITY = 80
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_upload(upload):
    if upload and upload.size > MAX_IMAGE_SIZE:
        raise ValidationError("Images must be 4 MB or smaller.")
    if upload and getattr(upload, "content_type", None) not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


def optimize_uploaded_image(upload):
    if not upload or not isinstance(upload, UploadedFile):
        return upload

    validate_image_upload(upload)
    upload.seek(0)
    try:
        with Image.open(upload) as img:
            img = ImageOps.exif_transpose(img)
            was_resized = max(img.size) > MAX_IMAGE_DIMENSION
            if was_resized:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

            content_type = getattr(upload, "content_type", "image/jpeg")
            stem = Path(upload.name).stem
            suffix = Path(upload.name).suffix.lower()
            buf = BytesIO()

            if content_type == "image/jpeg":
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=IMAGE_QUALITY, optimize=True, progressive=True)
                out_ext = suffix if suffix in (".jpg", ".jpeg") else ".jpg"
                out_ct = "image/jpeg"
            else:
                has_alpha = "A" in img.getbands() or (img.mode == "P" and "transparency" in img.info)
                target_mode = "RGBA" if has_alpha else "RGB"
                if img.mode != target_mode:
                    img = img.convert(target_mode)
                img.save(buf, format="WEBP", quality=IMAGE_QUALITY, method=4)
                out_ext = ".webp"
                out_ct = "image/webp"
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("Upload a valid JPEG, PNG, or WebP image.") from exc

    new_size = buf.getbuffer().nbytes
    if not was_resized and new_size >= upload.size and out_ct == getattr(upload, "content_type", None):
        upload.seek(0)
        return upload

    buf.seek(0)
    return InMemoryUploadedFile(
        buf,
        field_name=upload.field_name,
        name=f"{stem}{out_ext}",
        content_type=out_ct,
        size=new_size,
        charset=None,
    )


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    class Media:
        js = ("catalog/js/image-preview.js",)

    def clean_image(self):
        return optimize_uploaded_image(self.cleaned_data.get("image"))


class ItemImageAdminForm(forms.ModelForm):
    class Meta:
        model = ItemImage
        fields = "__all__"

    class Media:
        js = ("catalog/js/image-preview.js",)

    def clean_image(self):
        return optimize_uploaded_image(self.cleaned_data.get("image"))
