from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from ldap3 import Server, Connection
from services.upload_service import upload_to_api
from services.oracle_service import get_connection


# ================================
# LOGIN
# ================================
def login_view(request):

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # 1️⃣ cek user ke Oracle (RAW QUERY)
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, email, role
                FROM mst_user
                WHERE email = :1 
            """, [email])

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                messages.error(request, "User tidak terdaftar di sistem.")
                return redirect('login')

        except Exception as e:
            messages.error(request, f"Error database: {str(e)}")
            return redirect('login')

        # 2️⃣ cek AD
        server = Server('10.100.5.116', port=389)

        try:
            Connection(server, user=email, password=password, auto_bind=True)
        except:
            messages.error(request, "Username atau password salah.")
            return redirect('login')

        # 3️⃣ set session
        request.session['user_id'] = row[0]
        request.session['email'] = row[1]
        request.session['role'] = row[2]

        return redirect('dashboard')

    return render(request, 'login.html')


# ================================
# LOGOUT
# ================================
def logout_view(request):
    request.session.flush()
    return redirect('login')


# ================================
# CUSTOM LOGIN REQUIRED
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
@custom_login_required
def dashboard(request):

    conn = get_connection()
    cursor = conn.cursor()

    # Ambil data product (kalau memang masih perlu)
    cursor.execute("SELECT * FROM core_product")
    columns = [col[0].lower() for col in cursor.description]
    rows = cursor.fetchall()
    products = [dict(zip(columns, row)) for row in rows]

    # Hitung total langsung dari DB
    cursor.execute("SELECT COUNT(*) FROM core_product")
    total_product = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render(request, 'dashboard.html', {
        'products': products,
        'total_product': total_product
    })


# ================================
# CONFIG PRODUCT
# ================================
@custom_login_required
def config_product(request):

    if request.method == 'POST':

        try:
            conn = get_connection()
            cursor = conn.cursor()

            image_3d = upload_to_api(request.FILES['image_3d']) if request.FILES.get('image_3d') else None
            image_bird = upload_to_api(request.FILES['image_bird']) if request.FILES.get('image_bird') else None
            image_carton = upload_to_api(request.FILES['image_carton']) if request.FILES.get('image_carton') else None

            cursor.execute("""
                INSERT INTO core_product (
                    material_group,
                    material_number,
                    material_description,
                    pack_size_old,
                    base_unit,
                    order_unit,
                    sales_unit,
                    length,
                    width,
                    height,
                    qty_in_pallet,
                    qty_in_layers,
                    qty_layers,
                    image_3d,
                    image_bird,
                    image_carton
                )
                VALUES (
                    :1,:2,:3,:4,:5,:6,:7,
                    :8,:9,:10,
                    :11,:12,:13,
                    :14,:15,:16
                )
            """, [
                request.POST.get('material_group'),
                request.POST.get('material_number'),
                request.POST.get('material_description'),
                request.POST.get('pack_size_old'),
                request.POST.get('base_unit'),
                request.POST.get('order_unit'),
                request.POST.get('sales_unit'),
                request.POST.get('length') or None,
                request.POST.get('width') or None,
                request.POST.get('height') or None,
                request.POST.get('qty_in_pallet') or None,
                request.POST.get('qty_in_layers') or None,
                request.POST.get('qty_layers') or None,
                image_3d,
                image_bird,
                image_carton
            ])

            conn.commit()
            cursor.close()
            conn.close()

            messages.success(request, "Data berhasil disimpan.")
            return redirect('list_product')

        except Exception as e:
            messages.error(request, f"Gagal simpan: {str(e)}")

    return render(request, 'config_product.html', {"is_edit": False})


# ================================
# LIST PRODUCT
# ================================
@custom_login_required
def list_product(request):

    search = request.GET.get('search')

    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
SELECT id, material_number, material_description, material_group
FROM core_product
WHERE UPPER(material_number) LIKE UPPER(:search)
OR UPPER(material_description) LIKE UPPER(:search)
OR UPPER(material_group) LIKE UPPER(:search)
""", {"search": f"%{search}%"})
    else:
        cursor.execute("""
            SELECT id, material_number, material_description, material_group
            FROM core_product
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    products = [
        {
            "id": r[0],
            "material_number": r[1],
            "material_description": r[2],
            "material_group": r[3]
        }
        for r in rows
    ]

    return render(request, 'list_product.html', {"products": products})


# ================================
# PRODUCT DETAIL
# ================================
@custom_login_required
def product_detail(request, id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM core_product WHERE id = :1", [id])
    row = cursor.fetchone()

    columns = [col[0].lower() for col in cursor.description]
    product = dict(zip(columns, row)) if row else None

    cursor.close()
    conn.close()

    return render(request, 'product_detail.html', {"product": product})


# ================================
# GET MATERIAL DATA
# ================================
@custom_login_required
def get_material_data(request):

    material_number = request.GET.get("material_number")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
        WHERE MATERIAL_NUMBER = :1
    """, [material_number])

    row = cursor.fetchone()

    cursor.close()
    conn.close()

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


# ================================
# EDIT PRODUCT
# ================================
@custom_login_required
def edit_product(request, id):

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        image_3d = upload_to_api(request.FILES['image_3d']) if request.FILES.get('image_3d') else None
        image_bird = upload_to_api(request.FILES['image_bird']) if request.FILES.get('image_bird') else None
        image_carton = upload_to_api(request.FILES['image_carton']) if request.FILES.get('image_carton') else None

        cursor.execute("""
            UPDATE core_product
            SET qty_in_pallet = :1,
                qty_in_layers = :2,
                qty_layers = :3,
                image_3d = NVL(:4, image_3d),
                image_bird = NVL(:5, image_bird),
                image_carton = NVL(:6, image_carton)
            WHERE id = :7
        """, [
            request.POST.get('qty_in_pallet') or None,
            request.POST.get('qty_in_layers') or None,
            request.POST.get('qty_layers') or None,
            image_3d,
            image_bird,
            image_carton,
            id
        ])

        conn.commit()
        messages.success(request, "Data berhasil diupdate.")
        return redirect('list_product')

    cursor.execute("SELECT * FROM core_product WHERE id = :1", [id])
    row = cursor.fetchone()
    columns = [col[0].lower() for col in cursor.description]
    product = dict(zip(columns, row)) if row else None

    cursor.close()
    conn.close()

    return render(request, "config_product.html", {
        "product": product,
        "is_edit": True
    })