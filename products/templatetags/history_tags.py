from django import template

register = template.Library()

@register.filter
def get_field(instance, field_name):
    return getattr(instance, field_name, '')