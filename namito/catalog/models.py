import html
import re
from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import gettext_lazy as _
from PIL import Image as PILImage
import io
from django.core.files.base import ContentFile
from colorfield.fields import ColorField
from namito.users.models import User


class ProcessedImageModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.process_image()
        super().save(*args, **kwargs)

    def process_image(self):
        if self.image:
            pil_image = PILImage.open(self.image)
            if pil_image.format != 'WEBP':
                output_io_stream = io.BytesIO()
                pil_image.convert('RGB').save(output_io_stream, format='WEBP', quality=70)
                output_io_stream.seek(0)
                self.image = ContentFile(output_io_stream.read(), name=self.image.name.split('.')[0] + '.webp')


class StaticPage(ProcessedImageModel):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    meta_title = models.CharField(max_length=60, blank=True, null=True)
    meta_description = models.CharField(max_length=160, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Static Page'
        verbose_name_plural = 'Static Pages'
        ordering = ['title']


class Category(MPTTModel, models.Model):
    CATEGORY_TYPES = [
        (0, _("For men")),
        (1, _("For woman")),
        (2, _("For children")),
        (3, _("Unisex"))
    ]
    name = models.CharField(max_length=255)
    type = models.IntegerField(choices=CATEGORY_TYPES, default=3)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    image = models.ImageField(null=True, blank=True)
    background_color = ColorField(default='#FF0000', null=True)
    parent = TreeForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children",
                            verbose_name=_("Parent category"))
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    meta_title = models.CharField(max_length=59, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    promotion = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _("Categories")
        ordering = ["order", "name"]

    class MPTTMeta:
        order_insertion_by = ["name"]

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        counter = 0

        unique_slug = base_slug
        while Category.objects.filter(slug=unique_slug).exists():
            counter += 1
            unique_slug = f"{base_slug}-{counter}"

        self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="The name of the brand")
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True, help_text="The logo of the brand")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"


class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = ColorField(default='#FFFFFF', null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE,
                                 verbose_name=_("Category"))
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.PROTECT, blank=True, null=True)
    meta_title = models.CharField(max_length=59, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_image = models.ImageField(blank=True, null=True)
    keywords = models.JSONField(null=True, blank=True)
    min_price = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True)

    def generate_meta_description(self):
        if self.description:
            decoded_description = html.unescape(self.description)
            self.description = decoded_description
            first_sentence_match = re.match(r"^(.*?[.!?])", decoded_description)
            first_sentence = first_sentence_match.group(1) if first_sentence_match else decoded_description

            return first_sentence[:160]
        else:
            return ""

    def generate_meta_title(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.meta_description:
            self.meta_description = self.generate_meta_description()

        if not self.meta_title:
            self.meta_title = self.generate_meta_title()
        super().save(*args, **kwargs)


class Color(models.Model):
    name = models.CharField(max_length=50)
    color = ColorField(default='#FFFFFF')

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='variants')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(blank=True, null=True)
    DISCOUNT_TYPE_CHOICES = [
        ('percent', _("Percent")),
        ('unit', _("Unit")),
    ]
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text=_(
        "Discount amount, either in percentage or fixed unit based on the discount type."))
    discount_type = models.CharField(default=0, max_length=7, choices=DISCOUNT_TYPE_CHOICES, blank=True, null=True,
                                     help_text=_("Type of the discount - either a percent or a fixed unit."))

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"

    def get_price(self):
        if self.discount_value and self.discount_type:
            if self.discount_type == 'percent':
                discount_amount = (self.discount_value / 100) * self.price
                return self.price - discount_amount
            elif self.discount_type == 'unit':
                return self.price - self.discount_value
        return self.price


class Image(ProcessedImageModel):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    main_image = models.BooleanField(default=False)
    variant = models.ForeignKey(Variant, related_name='images', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} Image"


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE, verbose_name=_("Product"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    text = models.TextField(verbose_name=_("Text"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    def __str__(self):
        return f"{self.created_at} by {self.user}"

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ["-created_at"]


class ReviewImage(ProcessedImageModel):
    review = models.ForeignKey(Review, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='review_images/')
    main_image = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.review}"


class Rating(models.Model):
    product = models.ForeignKey(Product, related_name='ratings', on_delete=models.CASCADE, verbose_name=_("Product"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    score = models.PositiveIntegerField(default=4, verbose_name=_("Score"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    def __str__(self):
        return f"{self.score}/5 by {self.user.username}"

    class Meta:
        verbose_name = _("Rating")
        verbose_name_plural = _("Ratings")
        ordering = ["-created_at"]


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ['user', 'product']


class SizeChart(models.Model):
    categories = models.ManyToManyField(Category, related_name='size_charts')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SizeChartItem(models.Model):
    size_cart = models.ForeignKey(SizeChart, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)

    def __str__(self):
        return self.size
