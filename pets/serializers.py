from rest_framework import serializers

from .models import Pet, PetPhoto


class PetPhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PetPhoto
        fields = ("id", "url")

    def get_url(self, obj):
        request = self.context.get("request")
        if request and obj.url:
            return request.build_absolute_uri(obj.url)
        return obj.url


class PetSerializer(serializers.ModelSerializer):
    photos = PetPhotoSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model = Pet
        fields = ("id", "name", "age", "type", "photos", "created_at")
        read_only_fields = ("id", "created_at", "photos")

    def validate_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Age cannot be negative.")
        return value

    def validate_type(self, value):
        valid_types = [choice[0] for choice in Pet.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid pet type. Allowed values are: {', '.join(valid_types)}"
            )
        return value


class PetListSerializer(serializers.ModelSerializer):
    photos = PetPhotoSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model = Pet
        fields = ("id", "name", "age", "type", "photos", "created_at")


class PetDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of pet UUIDs to delete.",
    )
