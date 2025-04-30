from django.urls import path

from .views import PetListView, PetPhotoUploadView  # PetDetailView

urlpatterns = [
    # GET /pets/ (List)
    # POST /pets/ (Create)
    # DELETE /pets/ (Batch Delete)
    path("", PetListView.as_view(), name="pet-list"),
    # POST /pets/{id}/photo
    path("<uuid:id>/photo", PetPhotoUploadView.as_view(), name="pet-photo-upload"),
    # GET /pets/{id}
    # PUT /pets/{id}
    # PATCH /pets/{id}
    # DELETE /pets/{id}
    # path('<uuid:id>', PetDetailView.as_view(), name='pet-detail'),
]
