from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from .models import MyPlan
from .services import append_revision, create_plan, _verified


def _page(request, plans, error=''):
    from django.http import HttpResponse
    return HttpResponse(render_to_string('planning/my_plans.html', {'user':request.user,'csrf_token':get_token(request),'plans':plans,'error':error}))


@login_required(login_url='sign-in')
@require_http_methods(['GET','POST'])
@transaction.atomic
def my_plans(request):
    try:
        _verified(request.user)
    except PermissionDenied:
        return redirect('sign-in')
    if request.method == 'POST':
        try:
            if not request.POST.get('target', '').strip():
                raise ValidationError('A target is required.')
            with transaction.atomic():
                plan = create_plan(user=request.user)
                append_revision(user=request.user, plan=plan,
                    target={'text':request.POST.get('target','')},
                    assumptions={'text':request.POST.get('assumptions','')},
                    strategy_path={'text':request.POST.get('strategy_path','')})
            return redirect('my-plans')
        except (PermissionDenied, ValidationError):
            return _page(request, MyPlan.objects.filter(owner=request.user).prefetch_related('revisions'), 'We could not save this plan.')
    return _page(request, MyPlan.objects.filter(owner=request.user).prefetch_related('revisions').order_by('-updated_at'))


@login_required(login_url='sign-in')
@require_http_methods(['GET','POST'])
@transaction.atomic
def plan_revisions(request, plan_id):
    try:
        _verified(request.user)
    except PermissionDenied:
        return redirect('sign-in')
    plan = get_object_or_404(MyPlan.objects.prefetch_related('revisions'), pk=plan_id, owner=request.user)
    error = ''
    if request.method == 'POST':
        try:
            if not request.POST.get('target', '').strip():
                raise ValidationError('A target is required.')
            append_revision(user=request.user, plan=plan,
                target={'text':request.POST.get('target','')},
                assumptions={'text':request.POST.get('assumptions','')},
                strategy_path={'text':request.POST.get('strategy_path','')})
            return redirect('plan-revisions', plan_id=plan.pk)
        except (PermissionDenied, ValidationError):
            error = 'We could not save this revision. Please review the fields and try again.'
    from django.http import HttpResponse
    return HttpResponse(render_to_string('planning/plan_revisions.html', {'user':request.user,'csrf_token':get_token(request),'plan':plan,'revisions':plan.revisions.order_by('-revision_number'),'error':error}))
