from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

class ChangeLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_M2M_ADD = 'm2m_add'
    ACTION_M2M_REMOVE = 'm2m_remove'
    ACTION_M2M_CLEAR = 'm2m_clear'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_M2M_ADD, 'M2M Add'),
        (ACTION_M2M_REMOVE, 'M2M Remove'),
        (ACTION_M2M_CLEAR, 'M2M Clear'),
    ]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='changes')
    change_reason = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} on {self.content_type} #{self.object_id}"

class TrackedModel(models.Model):
    """Abstract model for change tracking"""
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Track changes on save"""
        from django.contrib.contenttypes.models import ContentType
        
        change_reason = kwargs.pop('change_reason', None)
        request = kwargs.pop('request', None)
        
        user = None
        ip_address = None
        user_agent = None
        
        if request and hasattr(request, 'user'):
            user = request.user if request.user.is_authenticated else None
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT')[:255] if request.META.get('HTTP_USER_AGENT') else None
        
        if self.pk:
            # Existing instance - track updates
            old_instance = self.__class__.objects.get(pk=self.pk)
            changes = self._get_field_changes(old_instance)
            
            if changes:  # Only log if there are actual changes
                ChangeLog.objects.create(
                    content_type=ContentType.objects.get_for_model(self.__class__),
                    object_id=self.pk,
                    action=ChangeLog.ACTION_UPDATE,
                    changes=changes,
                    user=user,
                    change_reason=change_reason,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
        else:
            # New instance - track creation
            ChangeLog.objects.create(
                content_type=ContentType.objects.get_for_model(self.__class__),
                object_id=self.pk,  # Will be None until saved
                action=ChangeLog.ACTION_CREATE,
                user=user,
                change_reason=change_reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        super().save(*args, **kwargs)
        
        # Update the creation log with the new PK if needed
        if not self.pk:
            ChangeLog.objects.filter(
                content_type=ContentType.objects.get_for_model(self.__class__),
                object_id=None,
                action=ChangeLog.ACTION_CREATE
            ).update(object_id=self.pk)
    
    def delete(self, *args, **kwargs):
        """Track deletions"""
        from django.contrib.contenttypes.models import ContentType
        
        change_reason = kwargs.pop('change_reason', None)
        request = kwargs.pop('request', None)
        
        user = None
        ip_address = None
        user_agent = None
        
        if request and hasattr(request, 'user'):
            user = request.user if request.user.is_authenticated else None
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT')[:255] if request.META.get('HTTP_USER_AGENT') else None
        
        ChangeLog.objects.create(
            content_type=ContentType.objects.get_for_model(self.__class__),
            object_id=self.pk,
            action=ChangeLog.ACTION_DELETE,
            user=user,
            change_reason=change_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        super().delete(*args, **kwargs)
    
    def _get_field_changes(self, old_instance):
        """Compare fields and return changes"""
        changes = {}
        
        for field in self._meta.fields:
            field_name = field.name
            
            # Skip fields that shouldn't be tracked
            if field_name in ['id', 'created_at', 'updated_at']:
                continue
                
            old_value = getattr(old_instance, field_name)
            new_value = getattr(self, field_name)
            
            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
        
        return changes or None

class Product(TrackedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name