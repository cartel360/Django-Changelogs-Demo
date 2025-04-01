from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'quantity']
    
    def __init__(self, *args, **kwargs):
        # Remove 'request' from kwargs before parent class initialization
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)