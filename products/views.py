from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product
from django.views.generic import DetailView
from django.contrib.contenttypes.models import ContentType
from .models import Product, ChangeLog

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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = ['name', 'description', 'price', 'quantity']
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.updated_by = request.user
        self.object.save(request=request)  # Pass request for logging
        return super().delete(request, *args, **kwargs)
    

class ProductChangeLogView(DetailView):
    model = Product
    template_name = 'products/product_changelog_custom.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content_type = ContentType.objects.get_for_model(Product)
        context['changes'] = ChangeLog.objects.filter(
            content_type=content_type,
            object_id=self.object.pk
        ).select_related('user').order_by('-timestamp')
        return context