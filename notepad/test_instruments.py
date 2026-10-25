"""Patch 20: Kenyan instrument models, checked against independent arithmetic and a published worked example."""
import json
from datetime import date
from decimal import Decimal as D

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from . import instruments as I
from . import rules
from .engine import EngineError


def metric(result, key):
    return next(m for m in result['metrics'] if m['key'] == key)['raw']


class RuleTests(TestCase):
    def test_every_rule_has_a_source(self):
        for r in rules.all_rules():
            self.assertTrue(r['url'].startswith('https://'), r['id'])
            self.assertTrue(r['source'] and r['retrieved'], r['id'])

    def test_known_rates(self):
        self.assertEqual(rules.rule('wht_tbill')['rate'], '15')
        self.assertEqual(rules.rule('wht_tbond_long')['rate'], '10')
        self.assertEqual(rules.rule('infrastructure_bond')['rate'], '0')

    def test_unknown_rule(self):
        with self.assertRaises(KeyError):
            rules.rule('nope')


class TBillTests(TestCase):
    def test_published_worked_example(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 364, 'yield_pct': 10})
        self.assertEqual(metric(r, 'price_per_100'), '90.9317')
        self.assertEqual(metric(r, 'first_cost'), '92291.98')
        self.assertEqual(metric(r, 'first_tax'), '1360.24')
        self.assertEqual(metric(r, 'net_gain'), '7708.02')

    def test_91_day_independent_formula(self):
        r = I.tbill({'amount': 500000, 'tenor_days': 91, 'yield_pct': 15.5})
        p = D(500000) / (1 + D('0.155') * 91 / 365)
        tax = (D(500000) - p) * D('0.15')
        self.assertEqual(metric(r, 'first_cost'), str((p + tax).quantize(D('0.01'))))

    def test_amount_as_cost_returns_face(self):
        a = I.tbill({'amount': 92291.98, 'amount_is': 'cost', 'tenor_days': 364, 'yield_pct': 10})
        self.assertEqual(metric(a, 'maturity_value'), '100000.00')

    def test_exempt_investor_pays_no_tax(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 182, 'yield_pct': 12, 'tax_exempt': True})
        self.assertEqual(metric(r, 'first_tax'), '0.00')

    def test_rollover_compounds(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 91, 'yield_pct': 12, 'rollovers': 4, 'amount_is': 'cost'})
        one = I.tbill({'amount': 100000, 'tenor_days': 91, 'yield_pct': 12, 'amount_is': 'cost'})
        per = D(metric(one, 'maturity_value')) / 100000
        self.assertAlmostEqual(float(metric(r, 'maturity_value')), float(100000 * per ** 4), delta=0.05)
        self.assertEqual(len(r['table']['rows']), 4)

    def test_rejects_bad_tenor_and_missing_yield(self):
        with self.assertRaises(EngineError) as c:
            I.tbill({'amount': 100000, 'tenor_days': 100})
        fields = [e['field'] for e in c.exception.errors]
        self.assertIn('tenor_days', fields)
        self.assertIn('yield_pct', fields)

    def test_rules_listed_and_sourced(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 364, 'yield_pct': 10})
        self.assertIn('wht_tbill', [x['id'] for x in r['rules']])
        self.assertTrue(any(a['kind'] == 'sourced' and a.get('url') for a in r['assumptions']))

    def test_override_marked_as_user_entered(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 364, 'yield_pct': 10, 'tax_rate': 10})
        self.assertTrue(any(w['code'] == 'tax_override' for w in r['warnings']))
        self.assertEqual(metric(r, 'first_tax'), '906.83')


class TBondTests(TestCase):
    def test_par_bond_prices_at_100(self):
        r = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 5, 'ytm_pct': 12})
        self.assertEqual(metric(r, 'price_per_100'), '100.0000')
        self.assertEqual(metric(r, 'tax_on_discount'), '0.00')

    def test_price_matches_closed_form(self):
        r = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 10, 'ytm_pct': 14})
        y = D('0.07'); c = D(6)
        p = c * (1 - (1 + y) ** -20) / y + 100 * (1 + y) ** -20
        self.assertEqual(metric(r, 'price_per_100'), str(p.quantize(D('0.0001'))))

    def test_wht_by_tenor(self):
        short = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 5, 'ytm_pct': 12})
        long_ = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 10, 'ytm_pct': 12})
        self.assertEqual(metric(short, 'coupon_net'), '5100.00')
        self.assertEqual(metric(long_, 'coupon_net'), '5400.00')

    def test_infrastructure_is_tax_free(self):
        r = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 15, 'ytm_pct': 12, 'infrastructure': True})
        self.assertEqual(metric(r, 'coupon_net'), '6000.00')

    def test_par_bond_net_yield(self):
        r = I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 5, 'ytm_pct': 12})
        # 12% coupon taxed at 15% = 10.2% a year, paid half-yearly -> compounded (1.051)^2 - 1
        self.assertAlmostEqual(float(metric(r, 'net_annual_return')), (1.051 ** 2 - 1) * 100, places=3)

    def test_half_years_only(self):
        with self.assertRaises(EngineError):
            I.tbond({'face': 100000, 'coupon_rate': 12, 'tenor_years': 5.3, 'ytm_pct': 12})

    def test_schedule_length_and_total(self):
        r = I.tbond({'face': 100000, 'coupon_rate': 10, 'tenor_years': 3, 'ytm_pct': 10})
        self.assertEqual(len(r['table']['rows']), 6)
        self.assertEqual(metric(r, 'net_income'), '25500.00')


class MmfTests(TestCase):
    def test_net_yield_has_no_tax(self):
        r = I.mmf({'initial': 100000, 'years': 1, 'yield_pct': 10, 'yield_basis': 'net'})
        self.assertEqual(metric(r, 'total_tax'), '0.00')
        self.assertAlmostEqual(float(metric(r, 'final_balance')), 110000, delta=0.5)

    def test_gross_yield_is_taxed(self):
        r = I.mmf({'initial': 100000, 'years': 1, 'yield_pct': 10})
        g, t = D(metric(r, 'total_growth')), D(metric(r, 'total_tax'))
        self.assertAlmostEqual(float(t / g), 0.15, places=3)

    def test_missing_yield(self):
        with self.assertRaises(EngineError):
            I.mmf({'initial': 1000, 'years': 1})


class SaccoTests(TestCase):
    def test_one_year_average_balance(self):
        r = I.sacco({'contribution': 1000, 'years': 1, 'dividend_pct': 10})
        avg = D(sum(range(1, 13))) * 1000 / 12
        self.assertEqual(metric(r, 'total_dividends'), str((avg * D('0.10')).quantize(D('0.01'))))
        self.assertEqual(metric(r, 'total_tax'), '32.50')

    def test_cash_payout_keeps_deposits_flat(self):
        a = I.sacco({'initial': 10000, 'years': 3, 'dividend_pct': 10, 'payout': 'cash'})
        self.assertEqual(metric(a, 'deposits_end'), '10000.00')
        self.assertEqual(metric(a, 'paid_out'), '2850.00')

    def test_reinvest_grows_faster(self):
        a = I.sacco({'initial': 10000, 'years': 3, 'dividend_pct': 10})
        self.assertGreater(D(metric(a, 'deposits_end')), D(10000) + D(2850))


class LoanTests(TestCase):
    def test_reducing_payment(self):
        r = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 12})
        self.assertEqual(metric(r, 'payment'), '8884.88')
        self.assertEqual(r['table']['rows'][-1][-1], '0.00')

    def test_flat_payment(self):
        r = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 12, 'method': 'flat'})
        self.assertEqual(metric(r, 'payment'), '9333.33')
        self.assertEqual(metric(r, 'total_interest'), '12000.00')

    def test_flat_costs_more_than_reducing(self):
        r = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 12, 'method': 'flat'})
        self.assertGreater(D(metric(r, 'equivalent_reducing')), D(12))

    def test_reducing_true_cost_equals_quoted(self):
        r = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 24})
        self.assertAlmostEqual(float(metric(r, 'nominal_apr')), 12, places=3)

    def test_fees_raise_true_cost(self):
        a = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 12})
        b = I.loan({'principal': 100000, 'rate_pct': 12, 'term_months': 12, 'processing_fee_pct': 3})
        self.assertGreater(D(metric(b, 'effective_rate')), D(metric(a, 'effective_rate')))
        self.assertEqual(metric(b, 'received'), '97000.00')

    def test_zero_rate(self):
        r = I.loan({'principal': 12000, 'rate_pct': 0, 'term_months': 12})
        self.assertEqual(metric(r, 'payment'), '1000.00')

    def test_principal_repaid_in_full(self):
        r = I.loan({'principal': 50000, 'rate_pct': 18, 'term_months': 18})
        self.assertAlmostEqual(sum(float(x[3]) for x in r['table']['rows']), 50000, delta=0.5)


class ContractTests(TestCase):
    def test_all_models_share_one_shape(self):
        samples = {
            'tbill': {'amount': 100000, 'tenor_days': 182, 'yield_pct': 11},
            'tbond': {'face': 100000, 'coupon_rate': 11, 'tenor_years': 4, 'ytm_pct': 12},
            'mmf': {'initial': 1000, 'contribution': 500, 'years': 2, 'yield_pct': 9},
            'sacco': {'contribution': 2000, 'years': 3, 'dividend_pct': 8},
            'loan': {'principal': 30000, 'rate_pct': 15, 'term_months': 6},
        }
        for model, inputs in samples.items():
            r = I.run(model, inputs)
            for key in ('model', 'version', 'as_of', 'inputs', 'headline', 'metrics', 'table', 'chart', 'warnings', 'assumptions',
                        'methodology', 'interpretation', 'rules'):
                self.assertIn(key, r, model + ' ' + key)
            self.assertEqual(r['model'], model)
            self.assertTrue(r['interpretation'])
            for s in r['chart']['series']:
                self.assertEqual(len(s['values']), len(r['chart']['x']), model)
            width = len(r['table']['columns'])
            self.assertTrue(all(len(row) == width for row in r['table']['rows']), model)
            json.dumps(r)
            # live blocks re-run from stored inputs: the echoed inputs must reproduce the same result
            again = I.run(model, r['inputs'])
            self.assertEqual(again['headline'], r['headline'], model)

    def test_sourced_tax_rate_is_not_saved_as_an_override(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 364, 'yield_pct': 10})
        self.assertIsNone(r['inputs']['tax_rate'])
        again = I.run('tbill', r['inputs'])
        self.assertTrue(any(a['kind'] == 'sourced' and a['label'] == 'Withholding tax rate' for a in again['assumptions']))
        typed = I.tbill({'amount': 100000, 'tenor_days': 364, 'yield_pct': 10, 'tax_rate': 10})
        self.assertEqual(typed['inputs']['tax_rate'], '10')

    def test_unknown_model(self):
        with self.assertRaises(EngineError):
            I.run('crypto', {})

    def test_inputs_must_be_object(self):
        with self.assertRaises(EngineError):
            I.tbill([])

    def test_as_of_selects_date(self):
        r = I.tbill({'amount': 100000, 'tenor_days': 91, 'yield_pct': 10, 'as_of': '2026-01-05'})
        self.assertEqual(r['as_of'], '2026-01-05')


@override_settings(SECURE_SSL_REDIRECT=False)
class InstrumentApiTests(TestCase):
    def setUp(self):
        cache.clear()
        u = UserAccount.objects.create_user('c@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(u)}

    def post(self, body, auth=True):
        return Client().post('/api/v1/calc/instrument/', data=json.dumps(body), content_type='application/json', **(self.auth if auth else {}))

    def test_requires_sign_in(self):
        self.assertEqual(self.post({'model': 'loan', 'inputs': {}}, auth=False).status_code, 401)

    def test_runs_and_stamps(self):
        r = self.post({'model': 'tbill', 'inputs': {'amount': 100000, 'tenor_days': 364, 'yield_pct': 10}})
        self.assertEqual(r.status_code, 200)
        out = json.loads(r.content)['result']
        self.assertEqual(out['model'], 'tbill')
        self.assertIn('calculated_at', out)

    def test_invalid_inputs_are_400_with_fields(self):
        r = self.post({'model': 'loan', 'inputs': {'principal': 'abc'}})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(json.loads(r.content)['error'], 'invalid_inputs')

    def test_unknown_model_is_400(self):
        self.assertEqual(self.post({'model': 'x', 'inputs': {}}).status_code, 400)

    def test_rules_endpoint(self):
        r = Client().get('/api/v1/calc/rules/', **self.auth)
        self.assertEqual(r.status_code, 200)
        body = json.loads(r.content)
        self.assertIn('tbill', body['models'])
        self.assertTrue(all(x['url'] for x in body['rules']))
