from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)

    _change_tracker = {} # Stores original field values

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store_original_values()

    def _store_original_values(self):
        """Store original field values when instance is loaded"""
        self._change_tracker = {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
            if field.name not in ['id', 'created_at', 'updated_at']
        }

    def get_changes(self):
        """Return dictionary of changed fields and their old/new values"""
        changes = {}
        for field in self._meta.fields:
            field_name = field.name
            if field_name in ['id', 'created_at', 'updated_at', 'updated_by']:
                continue
            
            old_value = self._change_tracker.get(field_name)
            new_value = getattr(self, field_name)
            
            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value),
                    'new': str(new_value),
                    'field_type': field.get_internal_type()
                }
        return changes

    def save(self, *args, **kwargs):
        """Override save to track changes and set updated_by"""
        if not self.pk:
            # New instance - no changes to track
            changes = None
        else:
            changes = self.get_changes()
            if not changes:
                # No actual changes - skip logging
                return super().save(*args, **kwargs)
        
        # Set updated_by if available
        from django.contrib.auth import get_user
        try:
            user = get_user(None)
            if user and user.is_authenticated:
                self.updated_by = user
        except:
            pass
        
        result = super().save(*args, **kwargs)
        
        # Create change log after saving
        if self.pk and changes:
            ChangeLog.objects.create(
                model_name=self.__class__.__name__,
                object_id=self.pk,
                action=ChangeLog.ACTION_UPDATE,
                changes=changes,
                user=self.updated_by,
            )
        return result

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} on {self.model_name} #{self.object_id}"


@receiver(pre_save, sender=Product)
def capture_product_changes(sender, instance, **kwargs):
    """Store original values before save"""
    if instance.pk:  # Only for existing instances
        instance._original_values = {
            field.name: getattr(instance, field.name)
            for field in instance._meta.fields
            if field.name not in ['id', 'created_at', 'updated_at']
        }

@receiver(post_save, sender=Product)
def log_product_change(sender, instance, created, **kwargs):
    action = ChangeLog.ACTION_CREATE if created else ChangeLog.ACTION_UPDATE
    
    changes = None
    if not created and hasattr(instance, '_original_values'):
        changes = {}
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in ['id', 'created_at', 'updated_at', 'updated_by']:
                continue
            
            original_value = instance._original_values.get(field_name)
            current_value = getattr(instance, field_name)
            
            if original_value != current_value:
                changes[field_name] = {
                    'old': str(original_value),
                    'new': str(current_value),
                    'field': field.verbose_name or field_name
                }
        
        if not changes:
            print("No actual changes detected")
            return
    
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=action,
        changes=changes,
        user=instance.updated_by,
    )
    print(f"Logged {action} for product {instance.pk}")

@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=ChangeLog.ACTION_DELETE,
        user=instance.updated_by,
    )