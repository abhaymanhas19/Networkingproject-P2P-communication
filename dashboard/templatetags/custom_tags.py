from django import template

register = template.Library()

@register.filter
def get_item_at_index(list, index):
    try:
        return list[index]
    except IndexError:
        return None
