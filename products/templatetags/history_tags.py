from django import template

register = template.Library()

@register.filter
def get_field(instance, field_name):
    return getattr(instance, field_name, '')


@register.filter
def diff_against(record, prev_record):
    return record.diff_against(prev_record)