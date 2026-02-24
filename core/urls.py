from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('config-product/', views.config_product, name='config_product'),
    path('list-product/', views.list_product, name='list_product'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path("get-material-data/", views.get_material_data, name="get_material_data"),
    path("edit-product/<int:id>/", views.edit_product, name="edit_product"),
]
