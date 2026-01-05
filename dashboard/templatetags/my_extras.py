from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# --- CE FILTRE EST ESSENTIEL POUR AFFICHER L'IMAGE ---
@register.filter
def auto_render(value):
    if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
        return mark_safe(f'<img src="{value}" style="height: 50px; border-radius: 4px; cursor: zoom-in;" onclick="window.open(this.src)">')
    return value


