from django import template

register = template.Library()

@register.filter
def field_type(field):
    return field.field.__class__.__name__

@register.filter
def is_disabled(field):
    return field.field.disabled

@register.filter
def is_required(field):
    return field.field.required