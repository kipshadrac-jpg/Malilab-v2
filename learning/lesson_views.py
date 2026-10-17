from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from content.models import Lesson
from content.public import resolve_public_revision
from .lesson_completion import mark_lesson_complete


@login_required(login_url='sign-in')
@require_POST
def complete(request, slug):
    _, revision = resolve_public_revision(Lesson, slug)   # 404 unless published
    try:
        mark_lesson_complete(user=request.user, lesson_revision=revision)
    except PermissionDenied:
        return redirect('sign-in')
    params = {k: request.POST[k] for k in ('module', 'playbook') if request.POST.get(k)}
    url = reverse('lesson-detail', args=[slug])
    return redirect(url + ('?' + urlencode(params) if params else ''))
