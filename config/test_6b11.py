"""Phase 6B.11: automated accessibility, caching and security checks across the real pages."""
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone

from content.models import (Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision,
                            Playbook, PlaybookModuleRecommendation, PlaybookRevision,
                            PracticeActivity, PracticeActivityRevision)
from content.test_admin import staff_client
from practice.services import create_attempt, submit_attempt

User = get_user_model()
KEY = '00000000-0000-0000-0000-0000000000e1'
INPUTLESS = {'hidden', 'submit', 'button'}


def publish(rev, identity):
    rev.status = 'published'; rev._allow_lifecycle_transition = True; rev.save()
    identity.current_published_revision = rev; identity.status = 'published'
    identity._allow_pointer_update = True; identity.save()


class Audit(HTMLParser):
    """Collects the facts needed for basic accessibility rules."""
    def __init__(self):
        super().__init__()
        self.lang = None; self.title = ''; self.in_title = False; self.h1 = 0; self.levels = []
        self.mains = []; self.skip = False; self.viewport = False
        self.label_for = set(); self.label_depth = 0; self.fields = []
        self.button = None; self.buttons = []; self.imgs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        elif tag == 'title': self.in_title = True
        elif tag == 'meta' and a.get('name') == 'viewport': self.viewport = True
        elif tag in ('h1', 'h2', 'h3', 'h4'):
            self.levels.append(int(tag[1]))
            if tag == 'h1': self.h1 += 1
        elif tag == 'main': self.mains.append(a.get('id'))
        elif tag == 'a' and 'skip-link' in (a.get('class') or '') and a.get('href') == '#main': self.skip = True
        elif tag == 'label':
            self.label_depth += 1
            if a.get('for'): self.label_for.add(a['for'])
        elif tag in ('input', 'textarea', 'select'):
            if not (tag == 'input' and a.get('type') in INPUTLESS):
                self.fields.append((a.get('id'), a.get('aria-label'), self.label_depth > 0))
        elif tag == 'button': self.button = [a.get('aria-label') or '', '']
        elif tag == 'img': self.imgs.append('alt' in a)

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        elif tag == 'label': self.label_depth -= 1
        elif tag == 'button' and self.button is not None:
            self.buttons.append((self.button[0] + self.button[1]).strip()); self.button = None

    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.button is not None: self.button[1] += data

    def problems(self):
        out = []
        if self.lang != 'en': out.append('html lang missing')
        if not self.title.strip(): out.append('empty <title>')
        if not self.viewport: out.append('no viewport meta')
        if self.h1 != 1: out.append(f'{self.h1} h1 headings')
        if self.levels and self.levels[0] != 1: out.append('first heading is not h1')
        if any(b - a > 1 for a, b in zip(self.levels, self.levels[1:])): out.append(f'heading level skipped {self.levels}')
        if self.mains != ['main']: out.append(f'main landmark problem {self.mains}')
        if not self.skip: out.append('no skip link')
        for fid, aria, wrapped in self.fields:
            if not (aria or wrapped or (fid and fid in self.label_for)): out.append(f'field {fid!r} has no label')
        if any(not text for text in self.buttons): out.append('button without text')
        if not all(self.imgs): out.append('image without alt')
        return out


def audit(response):
    parser = Audit(); parser.feed(response.content.decode()); return parser.problems()


class SiteFixtureMixin:
    def build_site(self):
        cache.clear()
        lesson = Lesson.objects.create(slug='les')
        self.lesson_rev = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='Sacco basics', summary='Intro',
            blocks=[{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': 'A sacco is a savings society.'}}])
        publish(self.lesson_rev, lesson)
        activity = PracticeActivity.objects.create(slug='prac')
        self.practice_rev = PracticeActivityRevision.objects.create(activity=activity, revision_number=1, title='Budget practice',
            instructions='Think.', prompt='Amounts.', response_schema={'schema_version': 1, 'questions': [
                {'id': 'saving', 'type': 'decimal_amount', 'label': 'Saving', 'required': False, 'constraints': {'currency': 'KES'}},
                {'id': 'why', 'type': 'long_text', 'label': 'Why', 'required': False, 'constraints': {'max_length': 500}},
                {'id': 'count', 'type': 'integer', 'label': 'How many', 'required': False},
                {'id': 'kind', 'type': 'single_choice', 'label': 'Kind', 'required': False, 'options': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}]},
                {'id': 'multi', 'type': 'multiple_choice', 'label': 'Many', 'required': False, 'options': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}]}]})
        publish(self.practice_rev, activity)
        module = Module.objects.create(slug='mod')
        self.module_rev = ModuleRevision.objects.create(module=module, revision_number=1, title='Saving module', description='D')
        ModuleLearningRequirement.objects.create(module_revision=self.module_rev, target_kind='lesson', lesson_revision=self.lesson_rev, classification='required', position=1)
        ModuleLearningRequirement.objects.create(module_revision=self.module_rev, target_kind='practice', practice_revision=self.practice_rev, classification='required', position=2)
        publish(self.module_rev, module)
        playbook = Playbook.objects.create(slug='pb')
        self.playbook_rev = PlaybookRevision.objects.create(playbook=playbook, revision_number=1, title='Start saving', summary='S', scenario='Sc')
        PlaybookModuleRecommendation.objects.create(playbook_revision=self.playbook_rev, module_revision=self.module_rev, position=1)
        publish(self.playbook_rev, playbook)
        from discovery.services import rebuild_published_projection
        for kind, rev in (('lesson', self.lesson_rev), ('practice', self.practice_rev), ('module', self.module_rev), ('playbook', self.playbook_rev)):
            rebuild_published_projection(content_kind=kind, revision=rev)
        self.user = User.objects.create_user('a11y@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


class AccessibilityAuditTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()

    def check(self, client, paths):
        failures = []
        for path in paths:
            response = client.get(path)
            if response.status_code != 200:
                failures.append(f'{path}: HTTP {response.status_code}'); continue
            failures += [f'{path}: {p}' for p in audit(response)]
        self.assertEqual(failures, [], '\n'.join(failures))

    def test_public_pages_meet_basic_accessibility_rules(self):
        self.check(Client(), ['/', '/playbooks/', '/playbooks/pb/', '/modules/', '/modules/mod/', '/lessons/les/?module=mod',
                              '/search/', '/search/?q=sacco', '/sign-in/', '/practice/prac/'])

    def test_signed_in_pages_meet_basic_accessibility_rules(self):
        c = Client(); c.force_login(self.user)
        attempt = create_attempt(user=self.user, practice_revision=self.practice_rev)
        done = create_attempt(user=self.user, practice_revision=self.practice_rev)
        submit_attempt(user=self.user, attempt_id=done.pk, responses={})
        c.post('/my-plan/', {'target': 'T', 'assumptions': 'A', 'strategy_path': 'P'})
        from planning.models import MyPlan
        plan = MyPlan.objects.get(owner=self.user)
        self.check(c, ['/', '/lessons/les/?module=mod', '/modules/mod/', '/practice/prac/', f'/practice/attempts/{attempt.pk}/',
                       f'/practice/attempts/{done.pk}/submitted/', '/progress/', '/notes/', '/lessons/les/notes/',
                       '/my-plan/', f'/my-plan/{plan.pk}/'])

    def test_staff_evaluation_pages_meet_basic_accessibility_rules(self):
        attempt = create_attempt(user=self.user, practice_revision=self.practice_rev)
        submit_attempt(user=self.user, attempt_id=attempt.pk, responses={})
        _, sc = staff_client('a11y-staff@example.com', 'reviewer')
        self.check(sc, ['/staff/evaluations/', f'/staff/evaluations/{attempt.pk}/'])

    def test_lesson_button_is_a_real_labelled_button(self):
        c = Client(); c.force_login(self.user)
        page = c.get('/lessons/les/?module=mod')
        self.assertContains(page, 'Mark this lesson as complete')


class CachingAndHeadersTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()

    def test_private_pages_are_never_cached(self):
        c = Client(); c.force_login(self.user)
        for path in ('/progress/', '/notes/', '/my-plan/', '/sign-in/'):
            cc = c.get(path).get('Cache-Control', '')
            self.assertIn('no-store', cc, path); self.assertIn('private', cc, path)

    def test_public_pages_are_not_cached_for_signed_in_users_but_vary_on_cookie(self):
        c = Client(); c.force_login(self.user)
        self.assertIn('no-store', c.get('/lessons/les/').get('Cache-Control', ''))
        anon = Client().get('/lessons/les/')
        self.assertNotIn('no-store', anon.get('Cache-Control', ''))
        self.assertIn('Cookie', anon.get('Vary', ''))

    def test_clickjacking_and_sniffing_protection_headers(self):
        response = Client().get('/')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class SecurityBehaviourTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()

    def test_state_changing_posts_require_a_csrf_token(self):
        c = Client(enforce_csrf_checks=True); c.force_login(self.user)
        for path in ('/my-plan/', '/lessons/les/notes/', '/lessons/les/complete/', '/practice/prac/attempts/', '/sign-out/', '/modules/mod/completion/'):
            self.assertEqual(c.post(path, {'target': 'x'}).status_code, 403, path)

    def test_private_pages_send_anonymous_visitors_to_sign_in(self):
        for path in ('/progress/', '/notes/', '/my-plan/', '/lessons/les/notes/'):
            response = Client().get(path)
            self.assertEqual(response.status_code, 302, path); self.assertIn('sign-in', response['Location'])

    def test_staff_routes_do_not_exist_for_the_public_or_learners(self):
        c = Client(); c.force_login(self.user)
        for client in (Client(), c):
            for path in ('/staff/evaluations/', '/staff/evaluations/1/'):
                self.assertEqual(client.get(path).status_code, 404, path)
        self.assertEqual(Client().get('/admin/').status_code, 302)

    def test_post_only_actions_reject_get(self):
        c = Client(); c.force_login(self.user)
        for path in ('/practice/prac/attempts/', '/lessons/les/complete/', '/sign-out/'):
            self.assertEqual(c.get(path).status_code, 405, path)

    def test_private_note_text_never_appears_in_public_search(self):
        c = Client(); c.force_login(self.user)
        c.post('/lessons/les/notes/', {'kind': 'note', 'body': 'zebra-private-thought'})
        self.assertNotContains(Client().get('/search/?q=zebra'), 'zebra-private-thought')
        self.assertNotContains(c.get('/search/?q=zebra'), 'zebra-private-thought')

    def test_sign_in_redirect_cannot_leave_the_site(self):
        response = self.client.post('/sign-in/', {'email': 'a11y@example.com', 'password': 'strong-password-123', 'next': 'https://evil.example/'})
        self.assertEqual(response.status_code, 302); self.assertEqual(response['Location'], '/')

    def test_submitted_attempt_belongs_to_one_learner_only(self):
        attempt = create_attempt(user=self.user, practice_revision=self.practice_rev)
        other = User.objects.create_user('o@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        oc = Client(); oc.force_login(other)
        self.assertEqual(oc.post(f'/practice/attempts/{attempt.pk}/submit/', {}).status_code, 404)
        attempt.refresh_from_db(); self.assertEqual(attempt.state, 'started')
