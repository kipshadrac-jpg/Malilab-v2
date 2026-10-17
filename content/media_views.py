from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from . import media
from .models import MediaAsset, PlaybookRevision
from .studio.access import staff_roles


def cover_image(request, key):
    """A cover picture: public once its playbook is live; before that, only for signed-in, verified staff."""
    asset = get_object_or_404(MediaAsset, asset_key=key, media_kind='image', status='available')
    live = PlaybookRevision.objects.filter(cover_asset=asset, status='published',
                                           playbook__current_published_revision_id=F('pk')).exists()
    if not live and not staff_roles(request.user):
        raise Http404
    path = media.file_path(asset)
    if path is None or not path.is_file():
        raise Http404
    response = HttpResponse(path.read_bytes(), content_type=asset.mime_type)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    response['Content-Disposition'] = 'inline'
    response['Cache-Control'] = 'public, max-age=86400' if live else 'private, no-store'
    return response
