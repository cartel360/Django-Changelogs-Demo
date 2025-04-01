from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, ChangeLog

@receiver(post_save, sender=Product)
def log_product_creation(sender, instance, created, **kwargs):
    """Handle creation logs (updates are handled in model.save())"""
    if created:
        ChangeLog.objects.create(
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            action=ChangeLog.ACTION_CREATE,
            user=instance.updated_by,
        )

@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    """Handle deletion logs"""
    ChangeLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=ChangeLog.ACTION_DELETE,
        user=instance.updated_by,
    )