from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, help_text="Customer-facing category name, such as Sofa or Bed.")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly name; leave blank to generate it automatically.")
    description = models.TextField(blank=True, help_text="Optional introduction shown at the top of this category.")
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
           validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
           help_text="Optional category image. Use JPEG, PNG, or WebP up to 4 MB."
    )
    is_active = models.BooleanField(default=True, help_text="Turn off to hide this category from the website.")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first in menus.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    STOCK_STATUS_CHOICES = [
        (IN_STOCK, "In stock"),
        (OUT_OF_STOCK, "Out of stock"),
    ]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items", help_text="Choose the furniture category for this item.")
    name = models.CharField(max_length=150, help_text="The name customers will see in the catalog.")
    slug = models.SlugField(max_length=180, unique=True, help_text="URL-friendly name; leave blank to generate it automatically.")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Regular selling price in INR.")
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="discount (%)",
        help_text="Discount percentage to apply to the regular price. Use 0 for no discount.",
    )
    description = models.TextField(help_text="Describe the item, its comfort, construction, and ideal use.")
    material = models.CharField(max_length=150, blank=True, help_text="Main materials, such as Sheesham wood or velvet.")
    dimensions = models.CharField(max_length=100, blank=True, help_text="Format: 72in L x 34in W x 30in H.")
    color_variants = models.CharField(max_length=255, blank=True, help_text="Comma-separated options, such as Grey, Beige, Maroon.")
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default=IN_STOCK, verbose_name="availability", help_text="Choose whether customers can currently inquire about this item.")
    warranty_info = models.CharField(max_length=255, blank=True, help_text="Warranty coverage customers should know about.")
    delivery_info = models.CharField(max_length=255, blank=True, help_text="Delivery or installation terms for this item.")
    is_featured = models.BooleanField(default=False, help_text="Show this item in the homepage featured section.")
    is_active = models.BooleanField(default=True, help_text="Turn off to hide this item without deleting it.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.discount is not None and self.discount > 100:
            raise models.ValidationError({"discount": "Discount percentage cannot be greater than 100."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percentage(self):
        return float(self.discount or 0)

    @property
    def has_discount(self):
        return bool(self.discount and self.discount > 0)

    @property
    def discounted_price(self):
        if not self.has_discount:
            return self.price
        discount_value = (self.price * (self.discount / 100))
        return max(self.price - discount_value, 0)


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to="items/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        help_text="Upload a JPEG, PNG, or WebP image up to 4 MB.",
    )
    alt_text = models.CharField(max_length=150, blank=True, help_text="Short description for accessibility and search engines.")
    is_primary = models.BooleanField(default=False, help_text="Use this image as the item thumbnail and first gallery image.")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first in the gallery.")

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name_plural = "Item images"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ItemImage.objects.filter(item=self.item, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
        if not ItemImage.objects.filter(item=self.item, is_primary=True).exists():
            ItemImage.objects.filter(pk=self.pk).update(is_primary=True)

    def delete(self, *args, **kwargs):
        was_primary = self.is_primary
        item = self.item
        super().delete(*args, **kwargs)
        if was_primary:
            replacement = item.images.order_by("display_order", "id").first()
            if replacement:
                replacement.is_primary = True
                replacement.save(update_fields=["is_primary"])

    def __str__(self):
        return self.alt_text or "Image for {}".format(self.item.name)