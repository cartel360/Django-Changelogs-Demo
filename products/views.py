from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product

class ProductListView(ListView):
    model = Product
    context_object_name = 'products'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    fields = ['name', 'description', 'price', 'quantity']
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = ['name', 'description', 'price', 'quantity']
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product-list')