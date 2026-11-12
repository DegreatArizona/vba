from django import template

register = template.Library()

@register.filter
def status_percentage(status):
    if status == 'Pending':
        return '20%'
    elif status == 'Approved':
        return '40%'
    elif status == 'Accepted':
        return '60%'
    elif status == 'Repairing':
        return '80%'
    elif status == 'Done':
        return '100%'
    return '0%'

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)