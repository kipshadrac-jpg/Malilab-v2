import base64
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from config.test_6b11 import audit
from content import covers, media
from content.models import EditorialReview, MediaAsset, ModuleRevision, PlaybookRevision
from content.studio import ai
from content.test_admin import staff_client
from content.test_studio import StudioBase

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==')
ENV = {'ANTHROPIC_API_KEY': 'sk-ant-cover-test'}


class ArtTests(SimpleTestCase):
    def test_every_combination_is_valid_xml_with_no_text_or_scripts(self):
        for motif in covers.MOTIFS:
            for palette in covers.PALETTES:
                for pattern in covers.PATTERNS:
                    svg = covers.render_svg(motif, palette, pattern)
                    root = ET.fromstring(svg)
                    self.assertTrue(root.tag.endswith('svg'))
                    self.assertNotIn(b'<script', svg)
                    self.assertNotIn(b'<text', svg)
                    self.assertNotIn(b'href', svg)
                    self.assertLess(len(svg), 20000)

    def test_unknown_choices_are_refused(self):
        for args in (('dragon', 'forest', 'dots'), ('coins', 'neon', 'dots'), ('coins', 'forest', 'stripes'),
                     ('coins"><script>', 'forest', 'dots')):
            with self.subTest(args=args), self.assertRaises(ValueError):
                covers.render_svg(*args)


class UploadSniffTests(SimpleTestCase):
    def test_only_real_png_jpeg_webp_are_accepted(self):
        self.assertEqual(media.sniff_upload(PNG), 'image/png')
        self.assertEqual(media.sniff_upload(b'\xff\xd8\xff\xe0' + b'0' * 20), 'image/jpeg')
        self.assertEqual(media.sniff_upload(b'RIFF\x00\x00\x00\x00WEBPVP8 '), 'image/webp')
        for bad in (b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', b'<html><body>hi</body></html>',
                    b'GIF89a....', b'%PDF-1.4', b'', b'MZ\x90\x00'):
            self.assertIsNone(media.sniff_upload(bad))


class MediaBase(TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = override_settings(MALILAB_MEDIA_DIR=self.tmp)
        patcher.enable()
        self.addCleanup(patcher.disable)
        cache.clear()


class StorageTests(MediaBase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user('m@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())

    def test_same_picture_and_description_is_stored_once(self):
        a = media.save_cover(PNG, 'image/png', 'A tiny test picture', origin='uploaded', user=self.user)
        b = media.save_cover(PNG, 'image/png', 'A  tiny   test picture', origin='uploaded', user=self.user)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(MediaAsset.objects.count(), 1)
        self.assertEqual(open(media.file_path(a), 'rb').read(), PNG)

    def test_a_new_description_is_a_new_immutable_row_sharing_the_file(self):
        a = media.save_cover(PNG, 'image/png', 'First description', origin='uploaded', user=self.user)
        b = media.save_cover(PNG, 'image/png', 'Second description', origin='uploaded', user=self.user)
        self.assertNotEqual(a.pk, b.pk)
        self.assertEqual(media.file_path(a), media.file_path(b))
        self.assertEqual(os.listdir(os.path.join(self.tmp, 'covers')), [os.path.basename(media.file_path(a))])
        with self.assertRaises(ValidationError):
            a.alt = 'x'
            a.byte_size = 5
            a.save()

    def test_rules(self):
        for alt in ('', '   ', 'x' * 201):
            with self.subTest(alt=alt), self.assertRaises(ValidationError):
                media.save_cover(PNG, 'image/png', alt, origin='uploaded', user=self.user)
        with self.assertRaises(ValidationError):
            media.save_cover(PNG, 'application/pdf', 'Fine', origin='uploaded', user=self.user)
        with self.assertRaises(ValidationError):
            media.save_cover(b'0' * (media.MAX_UPLOAD_BYTES + 1), 'image/png', 'Fine', origin='uploaded', user=self.user)
        self.assertFalse(MediaAsset.objects.exists())

    def test_the_record_says_where_it_came_from(self):
        asset = media.save_cover(PNG, 'image/png', 'A tiny test picture', origin='uploaded', user=self.user)
        self.assertEqual((asset.media_kind, asset.mime_type, asset.status, asset.byte_size), ('image', 'image/png', 'available', len(PNG)))
        self.assertEqual(asset.rights_metadata['origin'], 'uploaded')
        self.assertEqual(asset.rights_metadata['alt_text'], 'A tiny test picture')
        self.assertEqual(asset.rights_metadata['created_by'], 'm@example.com')


class CoverBase(StudioBase):
    """Studio roles plus an isolated media folder."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = override_settings(MALILAB_MEDIA_DIR=self.tmp)
        patcher.enable()
        self.addCleanup(patcher.disable)
        cache.clear()
        env = mock.patch.dict(os.environ, ENV)
        env.start()
        self.addCleanup(env.stop)

    def playbook(self, title='I want to save'):
        lesson = self.publish('lesson', self.new_lesson())
        self.author_c.post('/studio/new/module/', {'title': 'Start saving', 'description': 'd', f'inc_lesson-{lesson.pk}': 'on',
                                                    f'pos_lesson-{lesson.pk}': '1'})
        module = self.publish('module', ModuleRevision.objects.get(title='Start saving'))
        response = self.author_c.post('/studio/new/playbook/', {
            'title': title, 'summary': 'For people who want a first emergency fund.', 'scenario': 'You just got paid.',
            f'inc_module-{module.pk}': 'on', f'pos_module-{module.pk}': '1', f'rat_module-{module.pk}': 'Start here.'})
        self.assertEqual(response.status_code, 302, response.content[:800])
        return PlaybookRevision.objects.get(title=title)

    def cover_url(self, rev):
        return f'/studio/playbook/{rev.pk}/cover/'

    def choose(self, rev, **extra):
        data = {'do': 'manual', 'motif': 'sprout', 'palette': 'forest', 'pattern': 'dots', 'alt_text': 'A sprout beside coins'}
        return self.author_c.post(self.cover_url(rev), {**data, **extra})


class StudioCoverTests(CoverBase):
    def test_only_the_author_of_a_draft_playbook_can_reach_the_page(self):
        rev = self.playbook()
        self.assertEqual(self.author_c.get(self.cover_url(rev)).status_code, 200)
        other, other_c = staff_client('a2@example.com', 'author_editor')
        for client in (other_c, self.reviewer_c, self.approver_c, self.admin_c):
            self.assertEqual(client.get(self.cover_url(rev)).status_code, 404)
            self.assertEqual(client.post(self.cover_url(rev), {'do': 'remove'}).status_code, 404)
        self.assertEqual(Client().get(self.cover_url(rev)).status_code, 302)

    def test_once_sent_for_review_the_cover_is_locked(self):
        rev = self.playbook()
        self.act(self.author_c, 'playbook', rev, 'submit')
        self.assertEqual(self.author_c.get(self.cover_url(rev)).status_code, 404)

    def test_choosing_a_design_sets_the_cover_and_shows_it_in_the_preview(self):
        rev = self.playbook()
        response = self.choose(rev)
        self.assertEqual(response.status_code, 302, response.content[:600])
        rev.refresh_from_db()
        self.assertEqual(rev.cover_asset.rights_metadata['origin'], 'chosen_design')
        self.assertEqual(rev.cover_asset.mime_type, 'image/svg+xml')
        page = self.author_c.get(f'/studio/playbook/{rev.pk}/')
        self.assertContains(page, 'alt="A sprout beside coins"')
        self.assertContains(page, 'Change the cover image')
        self.assertContains(self.author_c.get(self.cover_url(rev)), 'Remove the cover')
        self.assertEqual(self.author_c.get(f'/media/cover/{rev.cover_asset.asset_key}/').status_code, 200)

    def test_a_blank_description_gets_a_standard_one(self):
        rev = self.playbook()
        self.choose(rev, alt_text='', motif='shield')
        rev.refresh_from_db()
        self.assertEqual(rev.cover_asset.rights_metadata['alt_text'], 'Illustration of a shield with a tick')

    def test_bad_design_choices_change_nothing(self):
        rev = self.playbook()
        response = self.choose(rev, motif='dragon')
        self.assertEqual(response.status_code, 200)
        rev.refresh_from_db()
        self.assertIsNone(rev.cover_asset)

    def test_editing_the_playbook_keeps_the_cover(self):
        rev = self.playbook()
        self.choose(rev)
        module = ModuleRevision.objects.get(title='Start saving')
        self.author_c.post(f'/studio/playbook/{rev.pk}/edit/', {
            'title': 'I want to save', 'summary': 'Edited summary.', 'scenario': '', f'inc_module-{module.pk}': 'on', f'pos_module-{module.pk}': '1'})
        rev.refresh_from_db()
        self.assertEqual(rev.summary, 'Edited summary.')
        self.assertIsNotNone(rev.cover_asset)

    def test_remove(self):
        rev = self.playbook()
        self.choose(rev)
        self.author_c.post(self.cover_url(rev), {'do': 'remove'})
        rev.refresh_from_db()
        self.assertIsNone(rev.cover_asset)
        self.assertEqual(MediaAsset.objects.count(), 1)       # the record stays; assets are never deleted

    def test_an_unknown_action_is_not_found(self):
        rev = self.playbook()
        self.assertEqual(self.author_c.post(self.cover_url(rev), {'do': 'explode'}).status_code, 404)

    def test_posts_need_a_csrf_token(self):
        rev = self.playbook()
        self.author_c.handler.enforce_csrf_checks = True
        self.assertEqual(self.author_c.post(self.cover_url(rev), {'do': 'remove'}).status_code, 403)

    def test_the_cover_page_is_accessible(self):
        rev = self.playbook()
        self.choose(rev)
        self.assertEqual(audit(self.author_c.get(self.cover_url(rev))), [])
        self.assertEqual(audit(self.author_c.get(f'/studio/playbook/{rev.pk}/')), [])


class UploadTests(CoverBase):
    def upload(self, rev, data=PNG, name='cover.png', ctype='image/png', **extra):
        fields = {'do': 'upload', 'image': SimpleUploadedFile(name, data, ctype), 'image_alt': 'People counting savings', 'rights': 'on'}
        fields.update(extra)
        return self.author_c.post(self.cover_url(rev), fields)

    def test_a_real_picture_is_accepted(self):
        rev = self.playbook()
        response = self.upload(rev)
        self.assertEqual(response.status_code, 302, response.content[:800])
        rev.refresh_from_db()
        self.assertEqual((rev.cover_asset.mime_type, rev.cover_asset.rights_metadata['origin']), ('image/png', 'uploaded'))
        self.assertEqual(open(media.file_path(rev.cover_asset), 'rb').read(), PNG)

    def test_dangerous_or_fake_files_are_refused(self):
        rev = self.playbook()
        cases = [(b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', 'x.svg', 'image/svg+xml'),
                 (b'<html><script>alert(1)</script></html>', 'x.png', 'image/png'),
                 (b'GIF89a......', 'x.gif', 'image/gif'), (b'%PDF-1.4 ...', 'x.png', 'image/png')]
        for data, name, ctype in cases:
            with self.subTest(name=name):
                response = self.upload(rev, data, name, ctype)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'not a PNG, JPEG or WebP')
        rev.refresh_from_db()
        self.assertIsNone(rev.cover_asset)
        self.assertFalse(MediaAsset.objects.exists())

    def test_too_big_is_refused(self):
        rev = self.playbook()
        response = self.upload(rev, PNG + b'0' * media.MAX_UPLOAD_BYTES)
        self.assertContains(response, 'under 2 MB')
        self.assertFalse(MediaAsset.objects.exists())

    def test_a_description_and_the_rights_box_are_required(self):
        rev = self.playbook()
        self.assertContains(self.upload(rev, image_alt=''), 'This field is required')
        response = self.author_c.post(self.cover_url(rev), {'do': 'upload', 'image': SimpleUploadedFile('c.png', PNG, 'image/png'),
                                                            'image_alt': 'Fine description'})
        self.assertContains(response, 'This field is required')
        self.assertFalse(MediaAsset.objects.exists())


class AICoverTests(CoverBase):
    def run_ai(self, rev, result=None, error=None):
        target = mock.patch('content.studio.ai.call_model', side_effect=error) if error else \
            mock.patch('content.studio.ai.call_model', return_value=result)
        with target as m:
            response = self.author_c.post(self.cover_url(rev), {'do': 'ai'})
        self.calls = m
        return response

    def test_the_ai_picks_from_the_fixed_art_and_the_choice_is_recorded(self):
        rev = self.playbook()
        response = self.run_ai(rev, {'motif': 'sprout', 'palette': 'sunrise', 'pattern': 'waves',
                                     'alt_text': 'Illustration of a sprout growing beside two coins'})
        self.assertEqual(response.status_code, 302, response.content[:800])
        rev.refresh_from_db()
        asset = rev.cover_asset
        self.assertEqual(asset.rights_metadata['origin'], 'ai_generated')
        self.assertEqual(asset.rights_metadata['design'], {'motif': 'sprout', 'palette': 'sunrise', 'pattern': 'waves'})
        self.assertEqual(open(media.file_path(asset), 'rb').read(), covers.render_svg('sprout', 'sunrise', 'waves'))
        event = EditorialReview.objects.get(playbook_revision=rev, action='ai_drafted')
        self.assertIn('sprout, sunrise, waves', event.comment)
        self.assertIn('I want to save', self.calls.call_args[0][1])
        self.assertIn('For people who want a first emergency fund.', self.calls.call_args[0][1])

    def test_invented_options_are_refused(self):
        rev = self.playbook()
        response = self.run_ai(rev, {'motif': 'dragon', 'palette': 'forest', 'pattern': 'dots', 'alt_text': 'A dragon'})
        self.assertContains(response, 'does not exist')
        rev.refresh_from_db()
        self.assertIsNone(rev.cover_asset)

    def test_a_poor_description_falls_back_to_a_standard_one(self):
        rev = self.playbook()
        self.run_ai(rev, {'motif': 'pie', 'palette': 'ocean', 'pattern': 'grid', 'alt_text': 'x'})
        rev.refresh_from_db()
        self.assertEqual(rev.cover_asset.rights_metadata['alt_text'], 'Illustration of a pie chart')

    def test_service_trouble_shows_a_message(self):
        rev = self.playbook()
        response = self.run_ai(rev, error=ai.AIError('The AI service is busy.'))
        self.assertContains(response, 'The AI service is busy.')

    def test_without_a_key_it_says_so_and_manual_still_works(self):
        rev = self.playbook()
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            page = self.author_c.get(self.cover_url(rev))
            response = self.author_c.post(self.cover_url(rev), {'do': 'ai'})
        self.assertContains(page, 'not switched on yet')
        self.assertContains(response, 'not switched on yet')
        self.assertEqual(self.choose(rev).status_code, 302)


class ServingAndPublicTests(CoverBase):
    def live_playbook(self):
        rev = self.playbook()
        self.choose(rev)
        rev.refresh_from_db()
        return self.publish('playbook', rev)

    def test_a_draft_cover_is_private_to_staff(self):
        rev = self.playbook()
        self.choose(rev)
        rev.refresh_from_db()
        url = f'/media/cover/{rev.cover_asset.asset_key}/'
        self.assertEqual(Client().get(url).status_code, 404)
        learner = get_user_model().objects.create_user('l@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        learner_c = Client()
        learner_c.force_login(learner)
        self.assertEqual(learner_c.get(url).status_code, 404)
        for client in (self.author_c, self.reviewer_c, self.admin_c):
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn('no-store', response['Cache-Control'])

    def test_a_live_cover_is_public_with_safe_headers(self):
        rev = self.live_playbook()
        response = Client().get(f'/media/cover/{rev.cover_asset.asset_key}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('sandbox', response['Content-Security-Policy'])
        self.assertIn('max-age=86400', response['Cache-Control'])
        self.assertTrue(response.content.startswith(b'<svg'))

    def test_unknown_or_missing_files_are_not_found(self):
        rev = self.live_playbook()
        self.assertEqual(Client().get('/media/cover/cover-nope/').status_code, 404)
        os.remove(media.file_path(rev.cover_asset))
        self.assertEqual(Client().get(f'/media/cover/{rev.cover_asset.asset_key}/').status_code, 404)

    def test_public_pages_show_the_cover_accessibly(self):
        rev = self.live_playbook()
        detail = Client().get(f'/playbooks/{rev.playbook.slug}/')
        self.assertContains(detail, '<img class="cover-image"')
        self.assertContains(detail, 'alt="A sprout beside coins"')
        self.assertContains(detail, f'/media/cover/{rev.cover_asset.asset_key}/')
        self.assertEqual(audit(detail), [])
        for path in ('/playbooks/', '/'):
            page = Client().get(path)
            self.assertContains(page, 'cover-thumb')
            self.assertEqual(audit(page), [])

    def test_playbooks_without_a_cover_still_render(self):
        rev = self.publish('playbook', self.playbook())
        for path in (f'/playbooks/{rev.playbook.slug}/', '/playbooks/', '/'):
            response = Client().get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'cover-image')
            self.assertNotContains(response, 'cover-thumb')

    def test_a_corrected_draft_starts_with_the_same_cover(self):
        rev = self.live_playbook()
        self.act(self.author_c, 'playbook', rev, 'new-draft')
        newer = PlaybookRevision.objects.get(revision_number=2)
        self.assertEqual(newer.cover_asset_id, rev.cover_asset_id)
