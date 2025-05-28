from django.urls import path
from . import views

app_name = 'kuning'

urlpatterns = [
    # SATWA URLs
    path('satwa/', views.list_satwa, name='list_satwa'),
    path('satwa/tambah/', views.tambah_satwa, name='tambah_satwa'),
    path('satwa/edit/<str:id>/', views.edit_satwa, name='edit_satwa'),  # Changed from int to str
    path('satwa/hapus/<str:id>/', views.hapus_satwa, name='hapus_satwa'),  # Changed from int to str
    
    # HABITAT URLs
    path('habitat/', views.list_habitat, name='list_habitat'),
    path('habitat/tambah/', views.tambah_habitat, name='tambah_habitat'),
    path('habitat/edit/<int:id>/', views.edit_habitat, name='edit_habitat'),
    path('habitat/detail/<int:id>/', views.detail_habitat, name='detail_habitat'),
    path('habitat/hapus/<int:id>/', views.hapus_habitat, name='hapus_habitat'),
]
