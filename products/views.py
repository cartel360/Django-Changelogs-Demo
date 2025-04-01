from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product
from django.views.generic import DetailView
from django.shortcuts import redirect
from django.contrib import messages


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


class ProductChangeLogView(DetailView):
    model = Product
    template_name = 'products/product_changelog_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all().select_related('history_user')
        return context
    

def revert_product(request, pk, history_id):
    product = Product.objects.get(pk=pk)
    historical = product.history.get(history_id=history_id)
    historical.instance.save()
    
    messages.success(request, f"Reverted product to version from {historical.history_date}")
    return redirect('product-changelog', pk=pk)