from django import template


register = template.Library()

@register.filter
def abs_value(value):
    try:
        return abs(value)
    except (ValueError, TypeError):
        return ""
    

@register.filter
def addcomma(value):
    try:
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return ""
    

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (ValueError, TypeError):
        return ""
