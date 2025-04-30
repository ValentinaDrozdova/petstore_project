import os
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from petstore import settings

from .models import Pet, PetPhoto
from .permissions import HasAPIKey
from .serializers import (PetDeleteSerializer, PetListSerializer,
                          PetPhotoSerializer, PetSerializer)


class PetListView(generics.ListCreateAPIView):
    """
    GET /pets: List pets with filtering and pagination.
    POST /pets: Create a new pet.
    DELETE /pets: Delete pet.
    """

    permission_classes = [HasAPIKey]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PetSerializer
        return PetListSerializer

    def get_queryset(self):
        """
        Returns the queryset filtered based on 'has_photos' query parameter.
        """
        queryset = Pet.objects.prefetch_related("photos").all()
        has_photos_param = self.request.query_params.get("has_photos")

        if has_photos_param is not None:
            has_photos = has_photos_param.lower() == "true"
            if has_photos:
                queryset = queryset.filter(photos__isnull=False).distinct()
            else:
                queryset = queryset.filter(photos__isnull=True)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Handles GET request, applies pagination, and returns structured response.
        """
        queryset = self.get_queryset()
        total_count = queryset.count()

        limit_param = self.request.query_params.get("limit")
        offset_param = self.request.query_params.get("offset")

        try:
            offset = int(offset_param) if offset_param else 0
            limit = int(limit_param) if limit_param else 20
            if offset < 0 or limit <= 0:
                raise ValueError("Limit must be positive and offset non-negative.")
        except (TypeError, ValueError):
            offset = 0
            limit = 20

        paginated_queryset = queryset[offset : offset + limit]
        serializer = self.get_serializer(
            paginated_queryset, many=True, context={"request": request}
        )

        return Response({"count": total_count, "items": serializer.data})

    def perform_create(self, serializer):
        serializer.save()

    def delete(self, request, *args, **kwargs):
        # Handle DELETE / pets request for batch deletion of pets based on a list of IDs in the request body.
        serializer = PetDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids_to_delete = serializer.validated_data["ids"]
        deleted_count = 0
        errors = []

        for pet_id in ids_to_delete:
            try:
                pet = Pet.objects.get(id=pet_id)
                photos_of_pet = pet.photos.all()
                for photo in photos_of_pet:
                    photo.delete()
                photo_dir_path = os.path.join(
                    settings.MEDIA_ROOT, "pet_photos", str(pet_id)
                )
                if os.path.exists(photo_dir_path):
                    os.rmdir(photo_dir_path)
                pet.delete()
                deleted_count += 1
            except Pet.DoesNotExist:
                errors.append(
                    {
                        "id": str(pet_id),
                        "error": "Pet with the matching ID was not found",
                    }
                )
            except Exception as e:
                errors.append(
                    {"id": str(pet_id), "error": f"Error during deletion: {str(e)}"}
                )

        response_data = {"deleted": deleted_count, "errors": errors}
        return Response(response_data, status=status.HTTP_200_OK)


class PetPhotoUploadView(views.APIView):
    """
    POST /pets/{id}/photo: Upload a photo for a specific pet.
    """

    permission_classes = [HasAPIKey]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, id):
        try:
            pet_id = uuid.UUID(str(id))
        except ValueError:
            return Response(
                {"error": "Invalid Pet ID format."}, status=status.HTTP_400_BAD_REQUEST
            )

        pet = get_object_or_404(Pet, id=pet_id)

        if "file" not in request.data:
            return Response(
                {"error": 'File not found in request (expected field "file").'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_obj = request.data["file"]

        try:
            photo_instance = PetPhoto.objects.create(pet=pet)
        except Exception as e:
            return Response(
                {"error": f"Could not create PetPhoto object in DB: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            photo_instance.image.save(file_obj.name, file_obj)
        except Exception as e:
            try:
                photo_instance.delete()
            except Exception:
                pass
            return Response(
                {"error": f"Could not save file via ImageField: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = PetPhotoSerializer(
            photo_instance, context={"request": request}
        )

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
#     """
#     GET /pets/{id}: Retrieve a pet.
#     PUT /pets/{id}: Update a pet.
#     PATCH /pets/{id}: Partially update a pet.
#     DELETE /pets/{id}: Delete a pet.
#     """
#     permission_classes = [HasAPIKey]
#     queryset = Pet.objects.all()
#     serializer_class = PetSerializer
#     lookup_field = 'id'
#
#     def perform_destroy(self, instance):
#         super().perform_destroy(instance)
