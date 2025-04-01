from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class ChangeLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]
    
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='changes')
    change_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} on {self.model_name} #{self.object_id}"

# Signal handlers
@receiver(post_save, sender=Product)
def log_product_change(sender, instance, created, **kwargs):
    action = ChangeLog.ACTION_CREATE if created else ChangeLog.ACTION_UPDATE
    
    # Get changes for updates
    changes = None
    if not created:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            changes = {}
            for field in instance._meta.fields:
                field_name = field.name
                if field_name in ['id', 'created_at', 'updated_at']:
                    continue
                
                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)
                
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value),
                        'new': str(new_value)
                    }
            if not changes:
                return  # No actual changes
        except sender.DoesNotExist:
            pass
    
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=action,
        changes=changes,
        user=instance.updated_by,
    )

@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=ChangeLog.ACTION_DELETE,
        user=instance.updated_by,
    )