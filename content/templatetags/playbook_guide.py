from django import template

from content.guide import guide_of, render_text

register = template.Library()


@register.filter
def guide(revision):
    return guide_of(revision)


@register.filter
def guide_text(text):
    return render_text(text or '')
