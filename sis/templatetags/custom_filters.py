from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def startswith(value, arg):
    if not value:
        return False
    return str(value).startswith(str(arg))

@register.filter
def ordinal(value):
    """Convert a number to ordinal format: 1 -> 1st, 2 -> 2nd, etc."""
    if value is None or value == '—':
        return '—'
    try:
        n = int(value)
    except (ValueError, TypeError):
        return value
    
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"
