from django import template
from datetime import datetime
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def to_milliseconds(value):
    """Convert seconds to milliseconds."""
    try:
        return f"{float(value) * 1000:.2f}"  # Multiply by 1000 and format to 2 decimal places
    except (ValueError, TypeError):
        return "Invalid Time"
    

