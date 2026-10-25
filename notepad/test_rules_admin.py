"""Patch 23: the tax rules kept in the database, read by the calculators, and the staff form."""
import json
from datetime import date, timedelta
from decimal import Decimal as D

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from . import instruments as I
from . import rules
from .admin import TaxRuleAdmin, TaxRuleForm
from .models import TaxRule


def good_form(**extra):
    data = {'rule_id': 'wht_tbill', 'label': 'Withholding tax on the discount of a Treasury bill', 'rate': '10', 'status': 'As stated.',
            'source': 'Finance Act', 'url': 'https://example.org/finance-act', 'retrieved': date.today().isoformat(), 'caveat': '', 'active': 'on'}
    data.update(extra)
    return TaxRuleForm(data)


class SeedTests(TestCase):
    def test_every_builtin_rule_is_seeded(self):
        self.assertEqual(TaxRule.objects.count(), sum(len(v) for v in rules.RULES.values()))
        self.assertEqual({r.rule_id for r in TaxRule.objects.all()}, set(rules.RULES))

    def test_database_values_match_the_code_defaults(self):
        for rid, versions in rules.RULES.items():
            self.assertEqual(rules.rule(rid)['rate'], versions[-1]['rate'], rid)

    def test_stamp_comes_from_the_database(self):
        self.assertTrue(rules.rule('wht_tbill')['stamp'].startswith('db'))


class LoaderTests(TestCase):
    def row(self, rid='wht_tbill'):
        return TaxRule.objects.get(rule_id=rid)

    def test_calculators_use_the_edited_rate(self):
        r = self.row()
        r.rate = D('10')
        r.save()
        self.assertEqual(rules.rule('wht_tbill')['rate'], '10')
        out = I.run('tbill', {'amount': 100000, 'amount_is': 'face', 'tenor_days': 364, 'yield_pct': 10})
        self.assertEqual(next(m['raw'] for m in out['metrics'] if m['key'] == 'first_tax'), '906.83')

    def test_editing_changes_the_stamp(self):
        before = rules.rule('wht_tbill')['stamp']
        r = self.row()
        r.rate = D('12')
        r.save()
        self.assertNotEqual(rules.rule('wht_tbill')['stamp'], before)

    def test_new_version_applies_from_its_date(self):
        old = self.row()
        future = TaxRule.objects.create(rule_id='wht_tbill', label=old.label, rate=D('20'), effective_from=date.today() + timedelta(days=30),
                                        status='s', source='s', url='https://example.org', retrieved=date.today())
        self.assertEqual(rules.rule('wht_tbill')['rate'], '15')
        self.assertEqual(rules.rule('wht_tbill', date.today() + timedelta(days=31))['rate'], '20')
        future.effective_from = date.today() - timedelta(days=1)
        future.save()
        self.assertEqual(rules.rule('wht_tbill')['rate'], '20')

    def test_drafts_are_ignored(self):
        self.row().copy_as_draft()
        self.assertEqual(TaxRule.objects.filter(rule_id='wht_tbill').count(), 2)
        self.assertEqual(rules.rule('wht_tbill')['rate'], '15')
        self.assertFalse(TaxRule.objects.get(rule_id='wht_tbill', active=False).active)

    def test_withdrawing_every_version_falls_back_to_the_code_values(self):
        TaxRule.objects.filter(rule_id='wht_tbill').update(active=False)
        out = rules.rule('wht_tbill')
        self.assertEqual(out['rate'], '15')
        self.assertEqual(out['stamp'], 'builtin')

    def test_unknown_rule_still_raises(self):
        with self.assertRaises(KeyError):
            rules.rule('not_a_rule')

    def test_results_list_the_stamp_of_each_rule_used(self):
        out = I.run('tbill', {'amount': 100000, 'tenor_days': 364, 'yield_pct': 10})
        for used in out['rules']:
            self.assertIn('stamp', used)


class FormTests(TestCase):
    def test_a_good_form_is_valid(self):
        form = good_form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_rate_limits(self):
        self.assertFalse(good_form(rate='120').is_valid())
        self.assertFalse(good_form(rule_id='tbill_day_basis', rate='0').is_valid())
        self.assertTrue(good_form(rule_id='tbill_day_basis', rate='365').is_valid())

    def test_source_must_be_https_and_not_from_the_future(self):
        self.assertFalse(good_form(url='http://example.org').is_valid())
        self.assertFalse(good_form(retrieved=(date.today() + timedelta(days=1)).isoformat()).is_valid())

    def test_unknown_rule_is_refused(self):
        self.assertFalse(good_form(rule_id='made_up').is_valid())

    def test_two_active_versions_cannot_start_on_the_same_day(self):
        start = date.today() + timedelta(days=10)
        good_form(effective_from=start.isoformat()).save()
        self.assertFalse(good_form(effective_from=start.isoformat()).is_valid())

    def test_admin_is_registered_and_history_cannot_be_deleted(self):
        from config.admin_site import admin_site
        self.assertTrue(admin_site.is_registered(TaxRule))
        self.assertFalse(TaxRuleAdmin(TaxRule, admin_site).has_delete_permission(None))

    def test_in_force_flag(self):
        from config.admin_site import admin_site
        a = TaxRuleAdmin(TaxRule, admin_site)
        current = TaxRule.objects.get(rule_id='wht_tbill')
        self.assertTrue(a.in_force(current))
        draft = current.copy_as_draft()
        self.assertFalse(a.in_force(draft))


@override_settings(SECURE_SSL_REDIRECT=False)
class RulesApiTests(TestCase):
    def test_rules_endpoint_lists_stamps(self):
        cache.clear()
        u = UserAccount.objects.create_user('e@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        r = Client().get('/api/v1/calc/rules/', HTTP_AUTHORIZATION='Bearer ' + issue_token(u))
        self.assertEqual(r.status_code, 200)
        body = json.loads(r.content)
        self.assertTrue(all(x['stamp'].startswith('db') for x in body['rules']))
