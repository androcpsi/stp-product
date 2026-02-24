from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login')),  # default redirect
    path('', include('core.urls')),               # semua route di core
]
