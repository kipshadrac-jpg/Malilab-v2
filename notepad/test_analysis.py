"""Patch 21: sensitivity and stress tests, checked against direct runs of the engine."""
import json
from decimal import Decimal as D

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from . import engine
from . import instruments as I
from .engine import EngineError

RAW = {'initial': '100000', 'contribution': '5000', 'years': '10', 'annual_return': '10', 'include_inflation': True, 'inflation': '5'}


def final(raw, real=False):
    s = engine.project(engine.normalize(raw))['summary']
    return D(s['final_real_balance'] if real else s['final_balance'])


class SensitivityTests(TestCase):
    def test_matches_direct_runs(self):
        r = I.run('sensitivity', RAW)
        row = next(x for x in r['table']['rows'] if x[0] == 'Expected yearly return')
        low = final({**RAW, 'annual_return': '8'}, real=True)
        high = final({**RAW, 'annual_return': '12'}, real=True)
        self.assertEqual(D(row[3]), low)
        self.assertEqual(D(row[4]), high)
        self.assertEqual(D(row[5]), abs(high - low))

    def test_ranked_by_swing(self):
        r = I.run('sensitivity', RAW)
        swings = [D(x[5]) for x in r['table']['rows']]
        self.assertEqual(swings, sorted(swings, reverse=True))
        self.assertEqual(len(r['bars']), len(r['table']['rows']))

    def test_only_relevant_factors(self):
        r = I.run('sensitivity', {'years': '10', 'annual_return': '8', 'contribution': '1000'})
        labels = [x[0] for x in r['table']['rows']]
        self.assertNotIn('Yearly inflation', labels)
        self.assertNotIn('Starting amount', labels)
        self.assertIn('Amount you save each period', labels)

    def test_echoes_inputs_so_it_can_refresh(self):
        r = I.run('sensitivity', RAW)
        self.assertEqual(I.run('sensitivity', r['inputs'])['headline'], r['headline'])

    def test_bad_inputs(self):
        with self.assertRaises(EngineError):
            I.run('sensitivity', {'annual_return': '8'})

    def test_lists_assumptions_with_kinds(self):
        r = I.run('sensitivity', RAW)
        self.assertTrue(any(a['kind'] == 'assumption' and a['label'] == 'Test steps' for a in r['assumptions']))
        self.assertTrue(r['warnings'])


class StressTests(TestCase):
    def test_base_row_matches_engine(self):
        r = I.run('stress', RAW)
        base = r['table']['rows'][0]
        self.assertEqual(D(base[2]), final(RAW))
        self.assertEqual(D(base[3]), final(RAW, real=True))
        self.assertEqual(D(base[4]), 0)

    def test_lower_returns_matches_direct_run(self):
        r = I.run('stress', RAW)
        row = next(x for x in r['table']['rows'] if x[0] == 'Lower returns')
        self.assertEqual(D(row[2]), final({**RAW, 'annual_return': '7'}))

    def test_every_stress_is_worse_than_base_in_todays_money(self):
        r = I.run('stress', RAW)
        for row in r['table']['rows'][1:]:
            self.assertLess(D(row[4]), 0, row[0])

    def test_pause_needs_contributions(self):
        r = I.run('stress', {'initial': '100000', 'years': '10', 'annual_return': '8'})
        self.assertNotIn('Two years without saving', [x[0] for x in r['table']['rows']])

    def test_short_horizon_skips_bad_year_and_pause(self):
        r = I.run('stress', {'initial': '100000', 'contribution': '1000', 'years': '1', 'annual_return': '8'})
        names = [x[0] for x in r['table']['rows']]
        self.assertNotIn('Two years without saving', names)
        self.assertNotIn('A bad year in the middle', names)
        self.assertIn('Lower returns', names)

    def test_target_column_only_with_target(self):
        without = I.run('stress', RAW)
        with_target = I.run('stress', {**RAW, 'target': '5000000'})
        self.assertEqual(len(with_target['table']['columns']), len(without['table']['columns']) + 1)

    def test_chart_lines_align(self):
        r = I.run('stress', RAW)
        for s in r['chart']['series']:
            self.assertEqual(len(s['values']), len(r['chart']['x']))

    def test_json_safe_and_contract(self):
        r = I.run('stress', RAW)
        json.dumps(r)
        for key in ('model', 'version', 'inputs', 'headline', 'metrics', 'table', 'chart', 'warnings', 'assumptions', 'methodology', 'interpretation', 'rules'):
            self.assertIn(key, r)


@override_settings(SECURE_SSL_REDIRECT=False)
class AnalysisApiTests(TestCase):
    def setUp(self):
        cache.clear()
        u = UserAccount.objects.create_user('d@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(u)}

    def test_runs_through_the_instrument_endpoint(self):
        for model in ('sensitivity', 'stress'):
            r = Client().post('/api/v1/calc/instrument/', data=json.dumps({'model': model, 'inputs': RAW}), content_type='application/json', **self.auth)
            self.assertEqual(r.status_code, 200, r.content)
            self.assertEqual(json.loads(r.content)['result']['model'], model)

    def test_invalid_inputs_are_400(self):
        r = Client().post('/api/v1/calc/instrument/', data=json.dumps({'model': 'stress', 'inputs': {'annual_return': '8'}}), content_type='application/json', **self.auth)
        self.assertEqual(r.status_code, 400)


CMP = {'amount': '100000', 'years': '5', 'options': [
    {'kind': 'tbill', 'yield_pct': '10', 'tenor_days': 364},
    {'kind': 'mmf', 'yield_pct': '11'},
    {'kind': 'sacco', 'yield_pct': '9'},
    {'kind': 'bank', 'yield_pct': '6'},
]}


class CompareOptionTests(TestCase):
    def test_tbill_matches_single_calculator(self):
        r = I.run('compare', CMP)
        row = next(x for x in r['table']['rows'] if x[0] == 'Treasury bill')
        one = I.run('tbill', {'amount': 100000, 'amount_is': 'cost', 'tenor_days': 364, 'yield_pct': 10})
        rate = D(next(m['raw'] for m in one['metrics'] if m['key'] == 'net_annual_return')) / 100
        self.assertAlmostEqual(float(row[2]), float(100000 * (1 + rate) ** 5), delta=0.02)

    def test_mmf_and_sacco_match_single_calculators(self):
        r = I.run('compare', CMP)
        rows = {x[0]: x for x in r['table']['rows']}
        mmf = I.run('mmf', {'initial': 100000, 'years': 5, 'yield_pct': 11})
        sacco = I.run('sacco', {'initial': 100000, 'years': 5, 'dividend_pct': 9})
        self.assertEqual(rows['Money market fund'][2], next(m['raw'] for m in mmf['metrics'] if m['key'] == 'final_balance'))
        self.assertEqual(rows['SACCO'][2], next(m['raw'] for m in sacco['metrics'] if m['key'] == 'deposits_end'))

    def test_sorted_best_first_and_headline_names_best(self):
        r = I.run('compare', CMP)
        finals = [D(x[2]) for x in r['table']['rows']]
        self.assertEqual(finals, sorted(finals, reverse=True))
        self.assertIn(r['table']['rows'][0][0], r['headline']['label'])

    def test_exempt_loses_nothing_to_tax(self):
        r = I.run('compare', {**CMP, 'tax_exempt': True})
        self.assertTrue(all(D(x[5]) == 0 for x in r['table']['rows']))

    def test_tax_costs_something_otherwise(self):
        r = I.run('compare', CMP)
        self.assertTrue(all(D(x[5]) > 0 for x in r['table']['rows']))

    def test_chart_aligned_and_starts_at_amount(self):
        r = I.run('compare', CMP)
        self.assertEqual(len(r['chart']['x']), 6)
        for s in r['chart']['series']:
            self.assertEqual(len(s['values']), 6)
            self.assertEqual(D(s['values'][0]), 100000)

    def test_duplicate_kinds_get_distinct_names(self):
        r = I.run('compare', {'amount': '50000', 'years': '3', 'options': [{'kind': 'mmf', 'yield_pct': '10'}, {'kind': 'mmf', 'yield_pct': '12'}]})
        self.assertEqual(len({x[0] for x in r['table']['rows']}), 2)

    def test_errors_name_the_option_field(self):
        with self.assertRaises(EngineError) as c:
            I.run('compare', {'amount': '50000', 'years': '3', 'options': [{'kind': 'mmf'}, {'kind': 'tbill', 'yield_pct': '10'}]})
        self.assertIn('options[0].yield_pct', [e['field'] for e in c.exception.errors])

    def test_needs_two_to_five_options(self):
        for options in ([], [{'kind': 'mmf', 'yield_pct': '10'}], [{'kind': 'mmf', 'yield_pct': '10'}] * 6):
            with self.assertRaises(EngineError):
                I.run('compare', {'amount': '50000', 'years': '3', 'options': options})

    def test_sourced_rules_and_rerun(self):
        r = I.run('compare', CMP)
        self.assertEqual({x['id'] for x in r['rules']}, {'wht_tbill', 'wht_mmf', 'wht_dividend_resident', 'wht_bank_interest'})
        self.assertEqual(I.run('compare', r['inputs'])['headline'], r['headline'])
        self.assertTrue(any('not automatically a better choice' in s for s in r['interpretation']))
