from django import forms
from django.contrib import messages
from django.shortcuts import redirect

from . import ai
from .access import page, studio_view
from .kinds import KINDS, ORDER

KIND_CHOICES = [(k, KINDS[k]['label']) for k in ORDER]


class BriefForm(forms.Form):
    kind = forms.ChoiceField(label='What should the AI draft?', choices=KIND_CHOICES)
    topic = forms.CharField(label='What is it about?', max_length=200,
                            help_text='For example: how a Sacco loan works, or building a first emergency fund.')
    audience = forms.CharField(label='Who is it for?', max_length=300, required=False,
                               help_text='For example: first-time earners in their twenties, or small traders using M-Pesa daily.')
    goal = forms.CharField(label='What should the learner be able to do afterwards?', max_length=600, required=False,
                           widget=forms.Textarea(attrs={'rows': 2}))
    flow = forms.CharField(label='How should it flow? (the order you want it to follow)', max_length=1500, required=False,
                           widget=forms.Textarea(attrs={'rows': 4}),
                           help_text='For example: start with a real situation, then the idea, then two options compared, then one small action.')
    focus = forms.CharField(label='What to focus on, and what to leave out', max_length=1500, required=False,
                            widget=forms.Textarea(attrs={'rows': 3}))
    tone = forms.ChoiceField(label='Tone', choices=[('friendly and practical', 'Friendly and practical'),
                                                   ('encouraging and simple', 'Encouraging and simple'),
                                                   ('calm and serious', 'Calm and serious')])
    length = forms.ChoiceField(label='Length (lessons and playbooks)', choices=[('short', 'Short, about 500 words'),
                                                                  ('medium', 'Medium, about 1,000 words'),
                                                                  ('long', 'Long, about 1,800 words')], initial='medium')
    question_count = forms.IntegerField(label='Number of questions (practice activities)', min_value=3, max_value=12,
                                        initial=6, required=False)
    material = forms.CharField(label='Facts, numbers and sources to use', max_length=ai.MAX_MATERIAL, required=False,
                               widget=forms.Textarea(attrs={'rows': 12}),
                               help_text='Paste your research here, with the source name beside each fact. The AI writes only from this and from basic, '
                                         'unchanging concepts. Anything it needs but does not have is listed for the reviewer to check.')


@studio_view('author_editor')
def start(request):
    if not ai.configured():
        return page(request, 'studio/ai_off.html')
    initial = {'kind': request.GET.get('kind') if request.GET.get('kind') in KINDS else 'lesson',
               'tone': 'friendly and practical'}
    form = BriefForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        from .views import _prerequisite          # same "publish parts first" rule as the normal editors
        brief = form.cleaned_data
        kind = brief['kind']
        problem = _prerequisite(kind)
        if problem:
            return page(request, 'studio/blocked.html', {'kind_label': KINDS[kind]['label'], 'problem': problem})
        try:
            revision, verify = ai.draft(kind, brief, request.user)
        except ai.AIError as exc:
            form.add_error(None, str(exc))
        else:
            tail = (f' {len(verify)} point(s) need checking; they are listed under History.' if verify
                    else ' Check every figure and claim before sending it for review.')
            messages.success(request, 'The AI draft is ready. Read it, edit anything you like, then send it for review.' + tail)
            return redirect('studio-revision', kind=kind, rev_id=revision.pk)
    return page(request, 'studio/ai_brief.html', {'form': form, 'model': ai.model_name()})
