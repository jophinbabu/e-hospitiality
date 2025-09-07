from django import template
from django.template.defaultfilters import stringfilter, timesince

register = template.Library()

@register.filter
@stringfilter
def split(value, separator):
    """Split a string by separator"""
    try:
        return value.split(separator)
    except (ValueError, AttributeError):
        return []

@register.filter  
def first(value):
    """Get the first item from a list"""
    try:
        return value[0] if value else ''
    except (IndexError, TypeError):
        return ''

@register.filter
def age_from_birth(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return "Not specified"
    
    age_string = timesince(date_of_birth)
    # Split by comma and return first part (e.g., "25 years, 3 months" -> "25 years")
    return age_string.split(',')[0] if ',' in age_string else age_string
