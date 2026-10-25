"""Reference tests for the calculation engine. Expected values come from independent closed-form formulas."""
import unittest
from decimal import Decimal, getcontext

from notepad import engine
from notepad.engine import EngineError, compare, normalize, project, solve

getcontext().prec = 50
D = Decimal


def run(**kw):
    base = {'years': 10}
    base.update(kw)
    return project(normalize(base))


def money(text):
    return D(text)


class ReferenceValues(unittest.TestCase):
    def test_lump_sum_monthly_compounding(self):
        r = run(initial=100000, annual_return=12, years=10)
        expected = D(100000) * (D('1.01') ** 120)
        self.assertAlmostEqual(float(money(r['summary']['final_balance'])), float(expected), places=2)

    def test_quarterly_compounding_matches_the_stated_convention_after_a_year(self):
        r = run(initial=1000, annual_return=12, years=1, compounding='quarterly')
        self.assertAlmostEqual(float(money(r['summary']['final_balance'])), float(D(1000) * D('1.03') ** 4), places=2)

    def test_effective_rate(self):
        r = run(initial=1000, annual_return=10, years=2, rate_type='effective')
        self.assertAlmostEqual(float(money(r['summary']['final_balance'])), 1210.0, places=2)

    def test_ordinary_annuity_end_of_month_contributions(self):
        i = D('0.01')
        n = 120
        expected = D(5000) * ((1 + i) ** n - 1) / i
        r = run(contribution=5000, annual_return=12)
        self.assertAlmostEqual(float(money(r['summary']['final_balance'])), float(expected), places=1)

    def test_annuity_due_start_of_month_contributions(self):
        i = D('0.01')
        n = 120
        expected = D(5000) * ((1 + i) ** n - 1) / i * (1 + i)
        r = run(contribution=5000, annual_return=12, contribution_timing='start')
        self.assertAlmostEqual(float(money(r['summary']['final_balance'])), float(expected), places=1)

    def test_zero_return_is_plain_addition(self):
        r = run(initial=1000, contribution=100, annual_return=0, years=2)
        self.assertEqual(r['summary']['final_balance'], '3400.00')
        self.assertEqual(r['summary']['total_contributed'], '3400.00')

    def test_fee_reduces_the_result_and_the_switch_removes_it(self):
        with_fee = run(initial=100000, annual_return=10, annual_fee=2)
        without = run(initial=100000, annual_return=10, annual_fee=2, include_fees=False)
        plain = run(initial=100000, annual_return=10)
        self.assertLess(money(with_fee['summary']['final_balance']), money(plain['summary']['final_balance']))
        self.assertEqual(without['summary']['final_balance'], plain['summary']['final_balance'])
        self.assertGreater(money(with_fee['summary']['total_fees']), 0)

    def test_tax_on_growth(self):
        taxed = run(initial=1000, annual_return=12, years=1, tax_on_growth=10)
        i = D('0.01')
        expected = D(1000) * (1 + i * D('0.9')) ** 12
        self.assertAlmostEqual(float(money(taxed['summary']['final_balance'])), float(expected), places=2)

    def test_real_value_uses_the_inflation_assumption(self):
        r = run(initial=1000, annual_return=0, years=2, inflation=10)
        self.assertAlmostEqual(float(money(r['summary']['final_real_balance'])), 1000 / 1.21, places=2)
        off = run(initial=1000, annual_return=0, years=2, inflation=10, include_inflation=False)
        self.assertIsNone(off['summary']['final_real_balance'])

    def test_yearly_increase_in_contribution(self):
        r = run(contribution=100, annual_return=0, years=2, annual_increase=10)
        self.assertEqual(r['summary']['total_contributed'], '2520.00')   # 12*100 + 12*110

    def test_pauses_and_stop_year(self):
        r = run(contribution=100, annual_return=0, years=2, pauses=[{'from_year': 0.5, 'to_year': 1}])
        self.assertEqual(r['summary']['total_contributed'], '1800.00')
        r = run(contribution=100, annual_return=0, years=2, contribution_end_year=1)
        self.assertEqual(r['summary']['total_contributed'], '1200.00')

    def test_quarterly_contributions(self):
        r = run(contribution=300, annual_return=0, years=1, contribution_frequency='quarterly')
        self.assertEqual(r['summary']['total_contributed'], '1200.00')

    def test_one_off_deposit_and_withdrawal(self):
        r = run(initial=1000, annual_return=0, years=2, lump_sums=[{'year': 1, 'amount': 500}, {'year': 1.5, 'amount': -200}])
        self.assertEqual(r['summary']['final_balance'], '1300.00')
        self.assertEqual(r['summary']['total_withdrawn'], '200.00')


class Withdrawals(unittest.TestCase):
    def test_fixed_withdrawal_present_value(self):
        i = D('0.01')
        n = 120
        capital = D(10000) * (1 - (1 + i) ** -n) / i
        r = run(initial=capital, annual_return=12, withdrawal={'mode': 'fixed', 'amount': 10000})
        self.assertIsNone(r['summary']['depletion_month'])
        self.assertLess(abs(money(r['summary']['final_balance'])), D('0.05'))

    def test_depletion_is_reported_and_balance_never_negative(self):
        r = run(initial=10000, annual_return=0, years=2, withdrawal={'mode': 'fixed', 'amount': 1000})
        self.assertEqual(r['summary']['depletion_month'], 11)
        self.assertEqual(r['summary']['final_balance'], '0.00')
        self.assertEqual(r['summary']['total_withdrawn'], '10000.00')
        self.assertTrue(any(w['code'] == 'depleted' for w in r['warnings']))
        self.assertTrue(all(money(row['closing']) >= 0 for row in r['annual']))

    def test_percent_of_starting_balance_and_of_current_balance(self):
        start = run(initial=120000, annual_return=0, years=1, withdrawal={'mode': 'pct_start', 'percent': 12})
        self.assertEqual(start['summary']['total_withdrawn'], '14400.00')
        current = run(initial=100000, annual_return=0, years=1, withdrawal={'mode': 'pct_current', 'percent': 12, 'frequency': 'annually'})
        self.assertEqual(current['summary']['total_withdrawn'], '12000.00')
        monthly = run(initial=100000, annual_return=0, years=1, withdrawal={'mode': 'pct_current', 'percent': 12})
        self.assertLess(money(monthly['summary']['total_withdrawn']), D(12000))     # shrinking balance, shrinking withdrawals

    def test_withdrawals_start_later(self):
        r = run(initial=10000, annual_return=0, years=2, withdrawal={'mode': 'fixed', 'amount': 100, 'start_year': 1})
        self.assertEqual(r['summary']['total_withdrawn'], '1200.00')

    def test_inflation_adjusted_withdrawal_grows_each_year(self):
        r = run(initial=100000, annual_return=0, years=2, inflation=10, withdrawal={'mode': 'inflation_adjusted', 'amount': 100})
        self.assertEqual(r['summary']['total_withdrawn'], '2520.00')


class Contract(unittest.TestCase):
    def test_accounting_identity_holds_every_year(self):
        r = run(initial=50000, contribution=3000, annual_return=9, annual_fee=1.5, tax_on_growth=15, years=7,
                withdrawal={'mode': 'fixed', 'amount': 500, 'start_year': 3}, lump_sums=[{'year': 2, 'amount': 4000}])
        for row in r['annual']:
            lhs = money(row['closing'])
            rhs = (money(row['opening']) + money(row['contributions']) + money(row['growth'])
                   - money(row['tax']) - money(row['fees']) - money(row['withdrawals']))
            self.assertLess(abs(lhs - rhs), D('0.05'), row)

    def test_same_inputs_same_outputs(self):
        a = run(initial=1234, contribution=56, annual_return=7.5)
        b = run(initial=1234, contribution=56, annual_return=7.5)
        self.assertEqual(a, b)

    def test_series_and_table_come_from_one_result(self):
        r = run(initial=1000, contribution=100, annual_return=5, years=3)
        self.assertEqual([row['closing'] for row in r['annual']], [p['closing'] for p in r['series'][1:]])
        self.assertEqual(r['series'][0]['closing'], '1000.00')
        self.assertEqual(r['annual'][-1]['closing'], r['summary']['final_balance'])

    def test_contract_fields(self):
        r = run(initial=1000, years=1, start_date='2026-01-31')
        for key in ('model', 'version', 'inputs', 'conventions', 'summary', 'annual', 'series', 'events', 'warnings', 'assumptions', 'methodology', 'interpretation'):
            self.assertIn(key, r)
        self.assertEqual(r['model'], 'compound-projection')
        self.assertEqual(r['annual'][0]['date'], '2027-01-31')
        detailed = project(normalize({'years': 1, 'initial': 100, 'start_date': '2026-01-31'}), detail=True)
        self.assertEqual(len(detailed['monthly']), 12)
        self.assertEqual(detailed['monthly'][1]['date'], '2026-03-31')

    def test_partial_years(self):
        r = run(initial=1000, years=2.5, annual_return=0)
        self.assertEqual(r['annual'][-1]['month'], 30)
        self.assertEqual(r['annual'][-1]['year'], '2.5')

    def test_interpretation_is_built_from_the_numbers_and_never_promises(self):
        r = run(initial=1000, contribution=100, annual_return=6, years=5, target=5000)
        text = ' '.join(r['interpretation'])
        self.assertIn(engine._commas(r['summary']['final_balance']), text)
        self.assertIn('not a forecast', text)

    def test_input_errors_name_the_field(self):
        with self.assertRaises(EngineError) as ctx:
            normalize({'years': 0, 'initial': 'abc', 'annual_return': 500, 'withdrawal': {'mode': 'fixed'}})
        fields = {e['field'] for e in ctx.exception.errors}
        self.assertTrue({'years', 'initial', 'annual_return', 'withdrawal.amount'} <= fields)
        with self.assertRaises(EngineError):
            normalize({'years': 5, 'initial': True})
        with self.assertRaises(EngineError):
            normalize({'years': 5, 'initial': 'NaN'})

    def test_extremes_do_not_break(self):
        r = run(initial=10 ** 12, contribution=10 ** 6, annual_return=100, years=80)
        self.assertTrue(money(r['summary']['final_balance']) > 0)
        r = run(initial=1000, annual_return=-50, years=80)
        self.assertTrue(money(r['summary']['final_balance']) >= 0)
        r = run(years=1)
        self.assertEqual(r['summary']['final_balance'], '0.00')

    def test_more_contribution_never_reduces_the_ending_balance(self):
        last = D(-1)
        for c in (0, 100, 250, 1000, 5000):
            final = money(run(initial=500, contribution=c, annual_return=4, annual_fee=1, years=6)['summary']['final_balance'])
            self.assertGreaterEqual(final, last)
            last = final


class Solvers(unittest.TestCase):
    def test_contribution_needed_for_a_target(self):
        base = normalize({'years': 10, 'annual_return': 12, 'target': 1000000})
        out = solve(base, 'contribution_for_target')
        i = D('0.01')
        expected = D(1000000) * i / ((1 + i) ** 120 - 1)
        self.assertAlmostEqual(float(out['solution']['value']), float(expected), delta=0.02)
        self.assertGreaterEqual(money(out['result']['summary']['final_balance']), D(1000000))

    def test_target_already_met(self):
        out = solve(normalize({'years': 5, 'initial': 2000, 'target': 1000}), 'contribution_for_target')
        self.assertEqual(out['solution']['value'], '0.00')

    def test_years_to_target(self):
        out = solve(normalize({'years': 5, 'initial': 1000, 'annual_return': 12, 'target': 2000}), 'years_to_target')
        # 1.01 ** n >= 2 -> n = 70 months
        self.assertEqual(out['solution']['months'], 70)

    def test_no_solution_is_explained(self):
        out = solve(normalize({'years': 5, 'initial': 1000, 'annual_return': 0, 'target': 10 ** 9}), 'years_to_target')
        self.assertIn('no_solution', out)
        self.assertIn('80 years', out['no_solution'])
        out = solve(normalize({'years': 5, 'target': 1000, 'annual_return': 0, 'initial': 0, 'withdrawal': {'mode': 'fixed', 'amount': 10 ** 10}}), 'contribution_for_target')
        self.assertIn('no_solution', out)

    def test_capital_for_a_withdrawal(self):
        base = normalize({'years': 10, 'annual_return': 12, 'withdrawal': {'mode': 'fixed', 'amount': 10000}})
        out = solve(base, 'capital_for_withdrawal')
        i = D('0.01')
        expected = D(10000) * (1 - (1 + i) ** -120) / i
        self.assertAlmostEqual(float(out['solution']['value']), float(expected), delta=0.05)
        self.assertIsNone(out['result']['summary']['depletion_month'])

    def test_largest_sustainable_withdrawal(self):
        i = D('0.01')
        capital = D(1000000)
        base = normalize({'years': 10, 'annual_return': 12, 'initial': 1000000, 'withdrawal': {'mode': 'fixed', 'amount': 1}})
        out = solve(base, 'max_withdrawal')
        expected = capital * i / (1 - (1 + i) ** -120)
        self.assertAlmostEqual(float(out['solution']['value']), float(expected), delta=0.05)

    def test_solver_errors(self):
        with self.assertRaises(EngineError):
            solve(normalize({'years': 5}), 'contribution_for_target')
        with self.assertRaises(EngineError):
            solve(normalize({'years': 5}), 'capital_for_withdrawal')
        with self.assertRaises(EngineError):
            solve(normalize({'years': 5}), 'nonsense')


class Scenarios(unittest.TestCase):
    BASE = {'years': 10, 'initial': 10000, 'contribution': 1000, 'annual_return': 8}

    def test_compare_reports_what_changed(self):
        out = compare(self.BASE, [{'name': 'Lower returns', 'overrides': {'annual_return': 4}},
                                  {'name': 'Save more', 'overrides': {'contribution': 2000}},
                                  {'name': 'Pull money out', 'overrides': {'withdrawal.mode': 'fixed', 'withdrawal.amount': 500}}])
        rows = out['scenarios']
        self.assertEqual([r['name'] for r in rows], ['Base case', 'Lower returns', 'Save more', 'Pull money out'])
        self.assertEqual(rows[1]['changes'], [{'field': 'annual_return', 'label': 'Assumed annual return (%)', 'from': '8', 'to': '4'}])
        self.assertLess(money(rows[1]['delta_final_balance']), 0)
        self.assertGreater(money(rows[2]['delta_final_balance']), 0)
        self.assertEqual(rows[3]['changes'][0]['field'], 'withdrawal.mode')

    def test_the_base_is_unchanged_by_scenarios(self):
        before = dict(self.BASE)
        compare(self.BASE, [{'name': 'x', 'overrides': {'annual_return': 1}}])
        self.assertEqual(self.BASE, before)

    def test_scenario_limits_and_errors(self):
        with self.assertRaises(EngineError):
            compare(self.BASE, [])
        with self.assertRaises(EngineError):
            compare(self.BASE, [{'name': str(i), 'overrides': {}} for i in range(6)])
        with self.assertRaises(EngineError) as ctx:
            compare(self.BASE, [{'name': 'bad', 'overrides': {'annual_return': 999}}])
        self.assertTrue(ctx.exception.errors[0]['field'].startswith('scenarios[0].'))


if __name__ == '__main__':
    unittest.main()
