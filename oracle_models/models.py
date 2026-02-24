from django.db import models

class MstUser(models.Model):
    email = models.CharField(max_length=100)
    status = models.IntegerField()
    role = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'MST_USER'
        app_label = 'oracle_models'


class CoreProduct(models.Model):

    material_group = models.CharField(max_length=50)
    material_number = models.CharField(max_length=50)
    material_description = models.CharField(max_length=200)
    pack_size_old = models.CharField(max_length=50, null=True, blank=True)
    base_unit = models.CharField(max_length=50, null=True, blank=True)
    order_unit = models.CharField(max_length=50, null=True, blank=True)
    sales_unit = models.CharField(max_length=50, null=True, blank=True)

    length = models.FloatField(null=True, blank=True)
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    qty_in_pallet = models.IntegerField(null=True, blank=True)
    qty_in_layers = models.IntegerField(null=True, blank=True)
    qty_layers = models.IntegerField(null=True, blank=True)
    image_3d = models.CharField(max_length=500, null=True, blank=True)
    image_bird = models.CharField(max_length=500, null=True, blank=True)
    image_carton = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        managed = False   # 🔥 WAJIB
        db_table = 'CORE_PRODUCT'
        app_label = 'oracle_models'