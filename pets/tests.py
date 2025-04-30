import os
import shutil
import uuid
from unittest.mock import Mock, PropertyMock, patch

from django.conf import settings
from django.core.files.uploadedfile import (InMemoryUploadedFile,
                                            SimpleUploadedFile)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Pet, PetPhoto

TEST_API_KEY = "test_api_key_123"


class PetAPITests(APITestCase):
    def setUp(self):
        """
        Setup before each test method.
        """
        self.client = APIClient()
        # Set the default API key for the client
        self.client.credentials(HTTP_X_API_KEY=TEST_API_KEY)

        # Clean and ensure the MEDIA_ROOT folder exists for tests
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        # Create test pets
        self.pet1 = Pet.objects.create(name="Rex", age=3, type="dog")
        self.pet2 = Pet.objects.create(name="Whiskers", age=2, type="cat")
        self.pet3 = Pet.objects.create(name="Buddy", age=5, type="dog")

        self.uploaded_image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00;"

    def tearDown(self):
        """
        Cleanup after each test method.
        """
        if os.path.exists(settings.MEDIA_ROOT):
            try:
                shutil.rmtree(settings.MEDIA_ROOT)
            except OSError as e:
                print(
                    f"Error removing MEDIA_ROOT {settings.MEDIA_ROOT} during tearDown: {e}"
                )

    # --- Tests for PetListView (GET /pets, POST /pets, DELETE /pets) ---

    def test_list_pets(self):
        """Test GET /pets - getting a list of pets."""
        url = reverse("pet-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        pet_ids_in_response = [item["id"] for item in response.data["items"]]
        self.assertIn(str(self.pet1.id), pet_ids_in_response)
        self.assertIn(str(self.pet2.id), pet_ids_in_response)
        self.assertIn(str(self.pet3.id), pet_ids_in_response)

    def test_list_pets_pagination(self):
        """Test GET /pets with pagination parameters."""
        url = reverse("pet-list")
        limit = 2
        offset = 1
        response = self.client.get(
            f"{url}?limit={limit}&offset={offset}", format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["items"]), limit)

    def test_list_pets_filter_has_photos(self):
        """Test GET /pets with the has_photos filter."""
        PetPhoto.objects.create(
            pet=self.pet1,
            image=SimpleUploadedFile("photo1.jpg", b"dummy", content_type="image/jpeg"),
        )
        url = reverse("pet-list")

        response_true = self.client.get(f"{url}?has_photos=true", format="json")
        self.assertEqual(response_true.status_code, status.HTTP_200_OK)
        self.assertEqual(response_true.data["count"], 1)
        self.assertEqual(response_true.data["items"][0]["id"], str(self.pet1.id))

        response_false = self.client.get(f"{url}?has_photos=false", format="json")
        self.assertEqual(response_false.status_code, status.HTTP_200_OK)
        self.assertEqual(response_false.data["count"], 2)
        pet_ids_false = [item["id"] for item in response_false.data["items"]]
        self.assertIn(str(self.pet2.id), pet_ids_false)
        self.assertIn(str(self.pet3.id), pet_ids_false)

    def test_create_pet(self):
        """Test POST /pets - creating a new pet."""
        url = reverse("pet-list")
        new_pet_data = {"name": "Barsik", "age": 1, "type": "cat"}
        response = self.client.post(url, new_pet_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pet.objects.count(), 4)
        self.assertEqual(response.data["name"], "Barsik")

    def test_create_pet_invalid_data(self):
        """Test POST /pets with invalid data."""
        url = reverse("pet-list")
        invalid_data = {"name": "InvalidPet", "age": -1}
        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pet.objects.count(), 3)
        self.assertIn("type", response.data)
        self.assertIn("age", response.data)

    def test_batch_delete_pets(self):
        """Test DELETE /pets - batch deletion of pets."""
        url = reverse("pet-list")

        pet_to_delete1 = Pet.objects.create(name="DeleteMe1", age=1, type="dog")
        pet_to_delete2 = Pet.objects.create(name="DeleteMe2", age=2, type="cat")
        pet_to_delete_nonexistent_id = uuid.uuid4()

        pet_with_photo_to_delete = Pet.objects.create(
            name="DeleteMeWithPhoto", age=4, type="cat"
        )
        uploaded_image1 = SimpleUploadedFile(
            "delete_photo1.gif", self.uploaded_image_content, content_type="image/gif"
        )
        uploaded_image2 = SimpleUploadedFile(
            "delete_photo2.gif", self.uploaded_image_content, content_type="image/gif"
        )
        photo1 = PetPhoto.objects.create(
            pet=pet_with_photo_to_delete, image=uploaded_image1
        )
        PetPhoto.objects.create(pet=pet_with_photo_to_delete, image=uploaded_image2)

        self.assertTrue(os.path.exists(photo1.image.path))
        photo_dir_path = os.path.join(
            settings.MEDIA_ROOT, "pet_photos", str(pet_with_photo_to_delete.id)
        )
        self.assertTrue(os.path.exists(photo_dir_path))

        ids_to_delete = [
            str(pet_to_delete1.id),
            str(pet_to_delete2.id),
            str(pet_with_photo_to_delete.id),
            str(self.pet1.id),
            str(pet_to_delete_nonexistent_id),
        ]

        response = self.client.delete(url, {"ids": ids_to_delete}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"], 4)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertEqual(
            response.data["errors"][0]["id"], str(pet_to_delete_nonexistent_id)
        )

        self.assertEqual(Pet.objects.count(), 2)
        self.assertEqual(PetPhoto.objects.count(), 0)
        self.assertFalse(os.path.exists(photo_dir_path))

    @patch("pets.views.PetPhoto.objects.create")
    def test_upload_pet_photo_mocked(self, mock_create):
        """
        Test POST /pets/{id}/photo - photo upload (mocked).
        Tests view logic without hitting DB or FS for save.
        """
        # --- Mock Setup ---
        mock_photo_instance = mock_create.return_value
        mock_photo_instance.id = uuid.uuid4()

        # Mock the image attribute and its save method
        mock_image_attribute = Mock()
        mock_photo_instance.image = mock_image_attribute
        mock_image_save = mock_image_attribute.save

        expected_relative_image_url = "/media/mock/path/mocked_photo.gif"
        mock_photo_instance.url = PropertyMock(return_value=expected_relative_image_url)

        mock_image_attribute.name = "pet_photos/mock/mocked_photo.gif"
        mock_image_attribute.path = (
            "/full/path/to/media/pet_photos/mock/mocked_photo.gif"
        )

        url = reverse("pet-photo-upload", args=[str(self.pet1.id)])
        uploaded_file = SimpleUploadedFile(
            "mock_upload.gif", self.uploaded_image_content, content_type="image/gif"
        )
        response = self.client.post(url, {"file": uploaded_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_create.assert_called_once_with(pet=self.pet1)

        self.assertEqual(mock_image_save.call_count, 1)

        # Get arguments from the call
        actual_positional_args = mock_image_save.call_args_list[0][0]
        actual_name = actual_positional_args[0]
        actual_file_obj_arg = actual_positional_args[1]

        # Assert arguments' attributes
        self.assertEqual(actual_name, uploaded_file.name)
        self.assertIsInstance(actual_file_obj_arg, InMemoryUploadedFile)
        self.assertEqual(actual_file_obj_arg.name, uploaded_file.name)
        self.assertEqual(actual_file_obj_arg.content_type, uploaded_file.content_type)

        # Assert response data structure and values
        self.assertIn("id", response.data)
        self.assertIn("url", response.data)
        self.assertEqual(response.data["id"], str(mock_photo_instance.id))

    def test_upload_pet_photo_integrated(self):
        """
        Test POST /pets/{id}/photo - photo upload (integrated).
        Tests full flow including DB and FS interaction.
        """
        url = reverse("pet-photo-upload", args=[str(self.pet2.id)])
        uploaded_file = SimpleUploadedFile(
            "integrated_photo.gif",
            self.uploaded_image_content,
            content_type="image/gif",
        )

        initial_photo_count = PetPhoto.objects.count()
        pet_photo_dir = os.path.join(
            settings.MEDIA_ROOT, "pet_photos", str(self.pet2.id)
        )
        self.assertFalse(
            os.path.exists(pet_photo_dir)
            and sum(1 for _ in os.scandir(pet_photo_dir)) > 0
        )

        response = self.client.post(url, {"file": uploaded_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PetPhoto.objects.count(), initial_photo_count + 1)

        created_photo_id = response.data["id"]
        created_photo = PetPhoto.objects.get(id=created_photo_id)

        self.assertEqual(created_photo.pet.id, self.pet2.id)
        self.assertTrue(created_photo.image)
        self.assertIn("pet_photos", created_photo.image.name)
        self.assertIn(str(self.pet2.id), created_photo.image.name)

        self.assertTrue(os.path.exists(created_photo.image.path))
        self.assertEqual(
            os.path.getsize(created_photo.image.path), len(self.uploaded_image_content)
        )

        self.assertIn("url", response.data)
        self.assertTrue(
            response.data["url"].startswith("http://testserver" + settings.MEDIA_URL)
        )
        self.assertIn(created_photo.image.name, response.data["url"])

    def test_upload_pet_photo_invalid_pet(self):
        """Test POST /pets/{id}/photo - non-existent pet."""
        non_existent_id = uuid.uuid4()
        url = reverse("pet-photo-upload", args=[str(non_existent_id)])
        uploaded_file = SimpleUploadedFile(
            "dummy.gif", b"dummy", content_type="image/gif"
        )
        response = self.client.post(url, {"file": uploaded_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(PetPhoto.objects.count(), 0)

    def test_upload_pet_photo_no_file(self):
        """Test POST /pets/{id}/photo - request without file."""
        url = reverse("pet-photo-upload", args=[str(self.pet1.id)])
        response = self.client.post(url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("File not found", response.data["error"])
        self.assertEqual(PetPhoto.objects.count(), 0)

    # --- Additional Tests ---

    def test_access_without_api_key(self):
        """Test access to views without API key."""
        client_without_key = APIClient()

        response_post_pet = client_without_key.post(
            reverse("pet-list"),
            {"name": "TestPerm", "age": 1, "type": "dog"},
            format="json",
        )
        self.assertEqual(
            response_post_pet.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"POST {reverse('pet-list')} failed permission check",
        )

        dummy_file = SimpleUploadedFile(
            "dummy.gif", b"content", content_type="image/gif"
        )
        response_post_photo = client_without_key.post(
            reverse("pet-photo-upload", args=[str(self.pet1.id)]),
            {"file": dummy_file},
            format="multipart",
        )
        self.assertEqual(
            response_post_photo.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"POST {reverse('pet-photo-upload', args=[str(self.pet1.id)])} failed permission check",
        )

        response_batch_delete = client_without_key.delete(
            reverse("pet-list"), {"ids": [str(self.pet1.id)]}, format="json"
        )
        self.assertEqual(
            response_batch_delete.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"DELETE {reverse('pet-list')} failed permission check",
        )

    def test_batch_delete_pets_empty_list(self):
        """Test DELETE /pets with empty list of IDs."""
        url = reverse("pet-list")
        ids_to_delete = []
        response = self.client.delete(url, {"ids": ids_to_delete}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pet.objects.count(), 3)
