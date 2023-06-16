from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path("previsualisation_download/",previsualisation_download, name="previsualisation_download"),
    path("liste_images/",liste_images, name="liste_images"),
    path("waterlevel/",waterlevel, name="waterlevel"),
    path("pretraitement/",pretraitement, name="pretraitement"),
    path("posttraitement/",posttraitement, name="posttraitement"),
    path("visualisation/",visualisation, name="visualisation"),
    path("classification/",classification, name="classification"),
    path("analyse/",analyse, name="analyse"),
    path("contact/",contact, name="contact"),
    path('download_satellite_image_from_id/<str:image_id>/', download_satellite_image_from_id, name='download_satellite_image_from_id'),
]
