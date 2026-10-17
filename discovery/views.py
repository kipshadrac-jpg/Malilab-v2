

def search(request):
    """Search only indexed editorial content, then revalidate current publication."""
    from django.db import connection
    from django.db.models import Q, F
    from django.http import HttpResponse
    from django.middleware.csrf import get_token
    from django.template.loader import render_to_string
    from .models import SearchProjection
    query = request.GET.get('q', '').strip()[:120]
    rows = SearchProjection.objects.none()
    if query:
        rows = SearchProjection.objects.all()
        if connection.vendor == 'postgresql':
            from django.contrib.postgres.search import SearchQuery
            rows = rows.filter(search_vector=SearchQuery(query, search_type='plain'))
        else:
            rows = rows.filter(Q(title__icontains=query) | Q(searchable_text__icontains=query))
        rows = rows.filter(
            Q(content_kind='playbook', playbook_revision__status='published', playbook_revision__playbook__status='published', playbook_revision__playbook__current_published_revision_id=F('playbook_revision_id'), playbook_revision__playbook_id=F('playbook_revision__playbook_id')) |
            Q(content_kind='module', module_revision__status='published', module_revision__module__status='published', module_revision__module__current_published_revision_id=F('module_revision_id'), module_revision__module_id=F('module_revision__module_id')) |
            Q(content_kind='lesson', lesson_revision__status='published', lesson_revision__lesson__status='published', lesson_revision__lesson__current_published_revision_id=F('lesson_revision_id'), lesson_revision__lesson_id=F('lesson_revision__lesson_id')) |
            Q(content_kind='practice', practice_revision__status='published', practice_revision__activity__status='published', practice_revision__activity__current_published_revision_id=F('practice_revision_id'), practice_revision__activity_id=F('practice_revision__activity_id'))
        ).select_related('playbook_revision__playbook','module_revision__module','lesson_revision__lesson','practice_revision__activity').order_by('content_kind','title','pk')[:50]
    return HttpResponse(render_to_string('discovery/search.html', {'user':request.user,'csrf_token':get_token(request),'query':query,'results':rows}))
