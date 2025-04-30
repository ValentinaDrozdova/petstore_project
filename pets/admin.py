from django.contrib import admin
from django.utils.html import mark_safe

from .models import Pet, PetPhoto


class PetPhotoInline(admin.TabularInline):
    model = PetPhoto
    extra = 0
    fields = ("image_thumbnail", "image", "uploaded_at")
    readonly_fields = ("image_thumbnail", "uploaded_at")

    def image_thumbnail(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />'
            )
        return "(No image)"

    image_thumbnail.short_description = "Preview"


class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "type", "created_at", "photo_count")
    search_fields = ("name", "type")
    list_filter = ("type", "age")
    inlines = [PetPhotoInline]

    def photo_count(self, obj):
        return obj.photos.count()

    photo_count.short_description = "Photos"


class PetPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "pet", "image_thumbnail", "uploaded_at")
    list_filter = ("pet", "uploaded_at")
    search_fields = ("pet__name",)

    def image_thumbnail(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />'
            )
        return "(No image)"

    image_thumbnail.short_description = "Image"


admin.site.register(Pet, PetAdmin)

admin.site.register(PetPhoto, PetPhotoAdmin)
