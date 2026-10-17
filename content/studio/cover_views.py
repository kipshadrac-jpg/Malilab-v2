from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect

from content import covers, media
from content.models import EditorialReview, PlaybookRevision
from content.services import ROLE_GROUPS
from . import ai, ai_cover
from .access import page, studio_view

MOTIF_CHOICES = [(m, covers.MOTIF_LABELS[m]) for m in covers.MOTIFS]
PALETTE_CHOICES = [(p, p.capitalize()) for p in covers.PALETTES]
PATTERN_CHOICES = [(p, p.capitalize()) for p in covers.PATTERNS]


class ManualForm(forms.Form):
    motif = forms.ChoiceField(label='Picture', choices=MOTIF_CHOICES)
    palette = forms.ChoiceField(label='Colours', choices=PALETTE_CHOICES)
    pattern = forms.ChoiceField(label='Background', choices=PATTERN_CHOICES)
    alt_text = forms.CharField(label='Describe the picture for people who cannot see it', max_length=media.MAX_ALT,
                               required=False, help_text='For example: Illustration of a sprout growing beside two coins. Leave blank to use a standard description.')


class UploadForm(forms.Form):
    image = forms.FileField(label='Picture file (PNG, JPEG or WebP, under 2 MB, ideally wide, 1200 by 630)')
    image_alt = forms.CharField(label='Describe the picture for people who cannot see it', max_length=media.MAX_ALT)
    rights = forms.BooleanField(label='I own this picture or have permission to use it on MaliLab')


def _revision(request, rev_id):
    try:
        rev = PlaybookRevision.objects.select_related('playbook', 'cover_asset').get(pk=rev_id)
    except PlaybookRevision.DoesNotExist:
        raise Http404
    if rev.status != 'draft' or rev.author_id != request.user.pk:
        raise Http404
    return rev


def _set(rev, asset):
    rev.cover_asset = asset
    rev.save()


def _context(rev, manual, upload):
    return {'rev': rev, 'manual_form': manual, 'upload_form': upload, 'ai_ready': ai.configured()}


@studio_view('author_editor')
def cover(request, rev_id):
    rev = _revision(request, rev_id)
    manual = ManualForm(initial={'motif': 'coins', 'palette': 'forest', 'pattern': 'dots'})
    upload = UploadForm()
    error = ''
    if request.method == 'POST':
        do = request.POST.get('do')
        try:
            if do == 'ai':
                if not ai.configured():
                    raise ai.AIError('The AI assistant is not switched on yet.')
                choice = ai_cover.design(rev, request.user)
                asset = media.save_cover(covers.render_svg(choice['motif'], choice['palette'], choice['pattern']), 'image/svg+xml',
                                         choice['alt_text'], origin='ai_generated', user=request.user,
                                         extra={'design': {k: choice[k] for k in ('motif', 'palette', 'pattern')},
                                                'licence': 'Original MaliLab artwork'})
                _set(rev, asset)
                EditorialReview.objects.create(content_kind='playbook', playbook_revision=rev, reviewer=request.user,
                                               role_snapshot=ROLE_GROUPS['author_editor'], action='ai_drafted',
                                               comment=f"Cover art chosen by the AI assistant ({ai.model_name()}): {choice['motif']}, {choice['palette']}, {choice['pattern']}.")
                messages.success(request, 'The AI designed a cover. You can try another design, choose your own, or upload a picture.')
                return redirect('studio-cover', rev_id=rev.pk)
            if do == 'manual':
                manual = ManualForm(request.POST)
                if manual.is_valid():
                    d = manual.cleaned_data
                    alt = d['alt_text'] or f"Illustration of {ai_cover.DESCRIPTIONS[d['motif']]}"
                    asset = media.save_cover(covers.render_svg(d['motif'], d['palette'], d['pattern']), 'image/svg+xml', alt,
                                             origin='chosen_design', user=request.user,
                                             extra={'design': {k: d[k] for k in ('motif', 'palette', 'pattern')},
                                                    'licence': 'Original MaliLab artwork'})
                    _set(rev, asset)
                    messages.success(request, 'Cover saved.')
                    return redirect('studio-cover', rev_id=rev.pk)
            elif do == 'upload':
                upload = UploadForm(request.POST, request.FILES)
                if upload.is_valid():
                    f = upload.cleaned_data['image']
                    data = f.read(media.MAX_UPLOAD_BYTES + 1)
                    if len(data) > media.MAX_UPLOAD_BYTES:
                        raise ValidationError('The picture must be under 2 MB.')
                    mime = media.sniff_upload(data)
                    if mime is None:
                        raise ValidationError('That file is not a PNG, JPEG or WebP picture.')
                    asset = media.save_cover(data, mime, upload.cleaned_data['image_alt'], origin='uploaded', user=request.user,
                                             extra={'licence': 'Uploaded by the author, who confirmed they may use it'})
                    _set(rev, asset)
                    messages.success(request, 'Cover uploaded.')
                    return redirect('studio-cover', rev_id=rev.pk)
            elif do == 'remove':
                _set(rev, None)
                messages.success(request, 'Cover removed.')
                return redirect('studio-cover', rev_id=rev.pk)
            else:
                raise Http404
        except ai.AIError as exc:
            error = str(exc)
        except ValidationError as exc:
            error = ' '.join(exc.messages)
    context = _context(rev, manual, upload)
    context['error'] = error
    return page(request, 'studio/cover.html', context)
