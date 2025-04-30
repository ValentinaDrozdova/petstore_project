import os
import uuid

from django.db import models
from django.utils import timezone


def pet_photo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/pet_photos/<pet_id>/<filename>
    return f"pet_photos/{instance.pet.id}/{filename}"


class Pet(models.Model):
    objects = None
    TYPE_CHOICES = (
        ("dog", "Dog"),
        ("cat", "Cat"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Name")
    age = models.PositiveIntegerField(verbose_name="Age")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    created_at = models.DateTimeField(
        default=timezone.now, editable=False, verbose_name="Creation Date"
    )

    def __str__(self):
        return f"{self.get_type_display()}: {self.name} ({self.age} years old)"

    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        ordering = ["-created_at"]


class PetPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(
        Pet, related_name="photos", on_delete=models.CASCADE, verbose_name="Pet"
    )
    image = models.ImageField(upload_to=pet_photo_path, verbose_name="Photo")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Upload Date")

    def __str__(self):
        return f"Photo {self.id} for {self.pet.name}"

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    @property
    def url(self):
        if self.image:
            return self.image.url
        return None

    class Meta:
        verbose_name = "Pet Photo"
        verbose_name_plural = "Pet Photos"
        ordering = ["-uploaded_at"]
