import json
from django import template

register = template.Library()

@register.filter
def get_item_at_index(list, index):
    try:
        return list[index]
    except IndexError:
        return None


@register.filter
def pretty_print(value):
    try:
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=3, sort_keys=True)
        else:
            return value
    except (ValueError, TypeError):
        return value


@register.simple_tag
def assign(value, var_name):
    return value


@register.filter
def keys_with_true_values(value):
    """
    Custom template filter that accepts a dictionary and returns a comma-separated
    string of keys whose values are True.
    
    Example:
    Input: {'key1': True, 'key2': False, 'key3': True}
    Output: "key1,key3"
    """
    if not isinstance(value, dict):
        return ""
    
    # Filter keys with True values and join them with commas
    return ",".join(key for key, val in value.items() if val)