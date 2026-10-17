"""Storage and records for cover images.

Files live in MALILAB_MEDIA_DIR (default: <project>/media/covers), named by the SHA-256 of their bytes.
Each distinct picture + description is one immutable MediaAsset row. Only the type is trusted from the
file's own first bytes, never from its name or what the browser claims.
"""
import hashlib
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import MediaAsset

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
EXTENSIONS = {'image/svg+xml': 'svg', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp'}
UPLOAD_TYPES = ('image/png', 'image/jpeg', 'image/webp')
MAX_ALT = 200


def media_root():
    return Path(getattr(settings, 'MALILAB_MEDIA_DIR', None) or Path(settings.BASE_DIR) / 'media')


def sniff_upload(data):
    """The image type of an upload from its first bytes, or None. SVG is deliberately never accepted from people."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return None


def clean_alt(alt):
    alt = ' '.join((alt or '').split())
    if not alt:
        raise ValidationError('Describe the picture in a short sentence, for people who cannot see it.')
    if len(alt) > MAX_ALT:
        raise ValidationError(f'Keep the picture description under {MAX_ALT} characters.')
    return alt


def file_path(asset):
    ext = EXTENSIONS.get(asset.mime_type)
    if ext is None or not asset.checksum.isalnum():
        return None
    return media_root() / 'covers' / f'{asset.checksum}.{ext}'


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.upload-')
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_cover(data, mime, alt, *, origin, user, extra=None):
    """Store the bytes and return the (possibly existing) immutable MediaAsset row."""
    if mime not in EXTENSIONS:
        raise ValidationError('That picture type is not allowed.')
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError('The picture must be under 2 MB.')
    alt = clean_alt(alt)
    checksum = hashlib.sha256(data).hexdigest()
    key = 'cover-' + hashlib.sha256(f'{checksum}|{alt}'.encode()).hexdigest()[:40]
    _write(media_root() / 'covers' / f'{checksum}.{EXTENSIONS[mime]}', data)
    asset, _ = MediaAsset.objects.get_or_create(asset_key=key, defaults={
        'media_kind': 'image', 'mime_type': mime, 'byte_size': len(data), 'checksum': checksum, 'status': 'available',
        'rights_metadata': {'purpose': 'playbook_cover', 'origin': origin, 'alt_text': alt,
                            'created_by': getattr(user, 'email', ''), **(extra or {})}})
    return asset
