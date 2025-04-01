from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChangeLog, Product
from django.views.generic import DetailView

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
    template_name = 'products/product_changelog.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['changes'] = ChangeLog.objects.filter(
            model_name='Product',
            object_id=self.object.pk
        ).select_related('user').order_by('-timestamp')
        return context