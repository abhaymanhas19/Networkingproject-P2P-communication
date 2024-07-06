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
