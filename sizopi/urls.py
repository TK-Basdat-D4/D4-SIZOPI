from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('adopsi/', include('adopsi.urls')),
    path('', lambda request: redirect('daftar_hewan')),  # <=== ini tambahan baru
]
