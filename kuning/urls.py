from django.urls import path
from . import views

urlpatterns = [
    path('satwa/', views.list_satwa, name='list_satwa'),
    path('satwa/tambah/', views.tambah_satwa, name='tambah_satwa'),
    path('satwa/edit/<int:id>/', views.edit_satwa, name='edit_satwa'),

    path('habitat/', views.list_habitat, name='list_habitat'),
    path('habitat/tambah/', views.tambah_habitat, name='tambah_habitat'),
    path('habitat/edit/<int:id>/', views.edit_habitat, name='edit_habitat'),
    path('habitat/detail/<int:id>/', views.detail_habitat, name='detail_habitat'),
]
