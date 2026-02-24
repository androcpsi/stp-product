from django import forms
from oracle_models.models import MstUser , CoreProduct

class ProductForm(forms.ModelForm):
    class Meta:
        model = CoreProduct
        fields = '__all__'
