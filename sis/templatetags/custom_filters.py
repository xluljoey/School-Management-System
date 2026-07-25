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
