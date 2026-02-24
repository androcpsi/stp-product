from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .forms import ProductForm
from oracle_models.models import MstUser , CoreProduct
from ldap3 import Server, Connection, ALL, SUBTREE
import os
from django.db import transaction
from services.upload_service import upload_to_api
from django.http import JsonResponse
from django.db import connections
from django.db.models.functions import Upper
from services.upload_service import upload_to_api


def login_view(request):

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # 1️⃣ cek ke Oracle dulu
        try:
            oracle_user = MstUser.objects.get(email=email, status=1)
        except MstUser.DoesNotExist:
            messages.error(request, "User tidak terdaftar di sistem.")
            return redirect('login')

        # 2️⃣ cek AD langsung
        server = Server('10.100.5.116', port=389)

        try:
            conn = Connection(
                server,
                user=email,
                password=password,
                auto_bind=True
            )
        except:
            messages.error(request, "Username atau password salah.")
            return redirect('login')

        # 3️⃣ set session
        request.session['user_id'] = oracle_user.id
        request.session['email'] = oracle_user.email
        request.session['role'] = oracle_user.role

        return redirect('dashboard')

    return render(request, 'login.html')


# ================================
# CUSTOM LOGOUT
# ================================
def logout_view(request):
    request.session.flush()
    return redirect('login')


# ================================
# CUSTOM LOGIN REQUIRED DECORATOR
# ================================
def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ================================
# DASHBOARD
# ================================
@custom_login_required
def dashboard(request):
    products = CoreProduct.objects.using('oracle_prod').all()
    return render(request, 'dashboard.html', {'products': products})


# ================================
# CONFIG PRODUCT
# ================================
@custom_login_required
def config_product(request):

    if request.method == 'POST':
        try:
            with transaction.atomic(using='oracle_prod'):

                image_3d = None
                image_bird = None
                image_carton = None

                # Upload gambar jika ada
                if request.FILES.get('image_3d'):
                    image_3d = upload_to_api(request.FILES['image_3d'])

                if request.FILES.get('image_bird'):
                    image_bird = upload_to_api(request.FILES['image_bird'])

                if request.FILES.get('image_carton'):
                    image_carton = upload_to_api(request.FILES['image_carton'])

                # Simpan ke Oracle
                CoreProduct.objects.using('oracle_prod').create(
                    material_group=request.POST.get('material_group'),
                    material_number=request.POST.get('material_number'),
                    material_description=request.POST.get('material_description'),
                    pack_size_old=request.POST.get('pack_size_old'),
                    base_unit=request.POST.get('base_unit'),
                    order_unit=request.POST.get('order_unit'),
                    sales_unit=request.POST.get('sales_unit'),

                    length=request.POST.get('length') or None,
                    width=request.POST.get('width') or None,
                    height=request.POST.get('height') or None,

                    qty_in_pallet=request.POST.get('qty_in_pallet') or None,
                    qty_in_layers=request.POST.get('qty_in_layers') or None,
                    qty_layers=request.POST.get('qty_layers') or None,

                    image_3d=image_3d,
                    image_bird=image_bird,
                    image_carton=image_carton,
                )

            messages.success(request, "Data dan gambar berhasil disimpan.")
            return redirect('list_product')

        except Exception as e:
            messages.error(request, f"Gagal simpan: {str(e)}")

    return render(request, 'config_product.html', {
    "is_edit": False
})


# ================================
# LIST PRODUCT
# ================================
@custom_login_required
def list_product(request):

    search_query = request.GET.get('search')

    products = CoreProduct.objects.using('oracle_prod').all()

    if search_query:
        products = products.filter(
            Q(material_number__icontains=search_query) |
            Q(material_description__icontains=search_query.upper()) |
            Q(material_group__icontains=search_query.upper())
        )

    context = {
        'products': products,
        'search_query': search_query
    }

    return render(request, 'list_product.html', context)


# ================================
# PRODUCT DETAIL
# ================================
@custom_login_required
def product_detail(request, id):
    product = CoreProduct.objects.using('oracle_prod').get(id=id)
    return render(request, 'product_detail.html', {'product': product})

# ================================
# GET DATA
# ================================

@custom_login_required
def get_material_data(request):
    material_number = request.GET.get("material_number")

    if not material_number:
        return JsonResponse({"error": "Material number kosong"}, status=400)

    query = """
        select * from (SELECT DISTINCT
            TRIM(TO_CHAR(TO_NUMBER(A.MATERIAL_NUMBER))) AS MATERIAL_NUMBER,
            A.MATERIAL_DESCRIPTION,
            A.MATERIAL_GROUP,
            A.BASE_UOM AS BASE_UNIT,
            A.ORDER_UNIT,
            B.SALES_UNIT,
            A.PACK_SIZE_OLD,
            A.LENGTH,
            A.WIDTH,
            A.HEIGHT
        FROM datagate.mara@datagate A
        LEFT JOIN (
            SELECT DISTINCT MATERIAL, SALES_UNIT 
            FROM datagate.mvke@datagate
        ) B ON A.MATERIAL_NUMBER = B.MATERIAL)
        WHERE MATERIAL_NUMBER = :material_number
    """

    with connections['oracle_prod'].cursor() as cursor:
        cursor.execute(query, {"material_number": material_number})
        row = cursor.fetchone()

    if not row:
        return JsonResponse({"error": "Material tidak ditemukan"}, status=404)

    return JsonResponse({
        "material_number": row[0],
        "material_description": row[1],
        "material_group": row[2],
        "base_unit": row[3],
        "order_unit": row[4],
        "sales_unit": row[5],
        "pack_size_old": row[6],
        "length": row[7],
        "width": row[8],
        "height": row[9],
    })
    
@custom_login_required
def edit_product(request, id):

    product = CoreProduct.objects.using('oracle_prod').get(id=id)

    if request.method == "POST":
        try:
            with transaction.atomic(using='oracle_prod'):

                # UPDATE FIELD KUNING
                product.qty_in_pallet = request.POST.get('qty_in_pallet') or None
                product.qty_in_layers = request.POST.get('qty_in_layers') or None
                product.qty_layers = request.POST.get('qty_layers') or None

                # === HANDLE IMAGE REPLACE ===

                if request.FILES.get('image_3d'):
                    new_url = upload_to_api(request.FILES['image_3d'])
                    if not new_url:
                        raise Exception("Upload 3D gagal")
                    product.image_3d = new_url

                if request.FILES.get('image_bird'):
                    new_url = upload_to_api(request.FILES['image_bird'])
                    if new_url:
                        product.image_bird = new_url

                if request.FILES.get('image_carton'):
                    new_url = upload_to_api(request.FILES['image_carton'])
                    if new_url:
                        product.image_carton = new_url

                product.save(using='oracle_prod')

            messages.success(request, "Data berhasil diupdate.")
            return redirect('list_product')

        except Exception as e:
            messages.error(request, f"Gagal update: {str(e)}")

    return render(request, "config_product.html", {
        "product": product,
        "is_edit": True
    })