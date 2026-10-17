from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def cover_url(asset):
    return reverse('cover-image', args=[asset.asset_key]) if asset else ''


@register.filter
def cover_alt(asset):
    meta = getattr(asset, 'rights_metadata', None)
    return meta.get('alt_text', '') if isinstance(meta, dict) else ''
