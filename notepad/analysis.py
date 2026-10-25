"""Advanced analysis on a savings projection: what matters most (sensitivity) and how it holds up when things go wrong (stress tests).

Both reuse the compound-projection engine, so every figure comes from the same tested model. Nothing here predicts anything:
the steps and shocks are examples chosen to show how much each assumption matters, and they are listed as assumptions in the result.
Each result uses the same shape as the instrument calculators (headline, metrics, table, chart, warnings, assumptions, ...).
"""
import copy
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .engine import EngineError, _m, apply_overrides, normalize, project
from . import rules as kenya_rules
from .engine import _dec
from .instruments import MODEL_VERSION, _assume, _finish, _int, _money, kes, mmf, pct, sacco, tbill

D = Decimal
ZERO = D(0)


def _text(v):
    t = format(D(v).normalize(), 'f')
    return '0' if t == '-0' else t


def _pp(v):
    return pct(v).replace('.00%', '%')


def _years(v):
    t = _text(v)
    return t + (' year' if t == '1' else ' years')


def _final(result, real):
    s = result['summary']
    if real and s.get('final_real_balance') is not None:
        return D(s['final_real_balance'])
    return D(s['final_balance'])


def _run(raw, **changes):
    merged = apply_overrides(raw, changes)
    return project(normalize(merged))


def _check(raw):
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    d = normalize(raw)
    return d, project(d)


def _clamp(v, low, high):
    return max(low, min(high, v))


def _base_assumptions(base, extra):
    rows = [dict(a) for a in base.get('assumptions', [])]
    return rows + extra


# ================================================================= sensitivity
def sensitivity(raw):
    d, base = _check(raw)
    real = bool(d['include_inflation']) and d['inflation'] > 0
    metric = "Final balance in today's money" if real else 'Final balance'
    base_val = _final(base, real)

    # (key, label, low, high, how to show a value)
    plan = []
    r = d['annual_return']
    plan.append(('annual_return', 'Expected yearly return', _clamp(r - 2, D(-50), D(100)), _clamp(r + 2, D(-50), D(100)), 'pct', '2 percentage points'))
    if d['contribution'] > 0:
        plan.append(('contribution', 'Amount you save each period', d['contribution'] * D('0.8'), d['contribution'] * D('1.2'), 'kes', '20%'))
    if d['initial'] > 0:
        plan.append(('initial', 'Starting amount', d['initial'] * D('0.8'), d['initial'] * D('1.2'), 'kes', '20%'))
    step = D(2) if d['years'] >= 6 else D(1)
    if d['years'] - step >= 1:
        plan.append(('years', 'How long you keep going', d['years'] - step, _clamp(d['years'] + step, D(1), D(80)), 'years', _years(step)))
    if real:
        plan.append(('inflation', 'Yearly inflation', _clamp(d['inflation'] - 2, D(-10), D(100)), _clamp(d['inflation'] + 2, D(-10), D(100)), 'pct', '2 percentage points'))
    if d['include_fees'] and d['annual_fee'] > 0:
        plan.append(('annual_fee', 'Yearly fee', _clamp(d['annual_fee'] - 1, ZERO, D(20)), _clamp(d['annual_fee'] + 1, ZERO, D(20)), 'pct', '1 percentage point'))
    if d['include_tax'] and d['tax_on_growth'] > 0:
        plan.append(('tax_on_growth', 'Tax on growth', _clamp(d['tax_on_growth'] - 5, ZERO, D(60)), _clamp(d['tax_on_growth'] + 5, ZERO, D(60)), 'pct', '5 percentage points'))

    def show(kind, v):
        return {'pct': _pp, 'kes': kes, 'years': _years}[kind](v)

    rows, notes = [], []
    for key, label, lo, hi, kind, step_text in plan:
        try:
            lo_final = _final(_run(raw, **{key: _text(lo)}), real)
            hi_final = _final(_run(raw, **{key: _text(hi)}), real)
        except EngineError:
            continue
        rows.append({'key': key, 'label': label, 'kind': kind, 'step': step_text, 'lo': lo, 'hi': hi, 'lo_final': lo_final, 'hi_final': hi_final,
                     'lo_delta': lo_final - base_val, 'hi_delta': hi_final - base_val, 'swing': abs(hi_final - lo_final)})
    rows.sort(key=lambda x: x['swing'], reverse=True)
    if not rows:
        raise EngineError([{'field': 'inputs', 'message': 'There is nothing to vary yet. Enter a return and an amount to save.'}])

    top = rows[0]
    table = {
        'title': 'What happens to the ' + metric.lower() + ' if one thing changes',
        'columns': [{'key': 'factor', 'label': 'What changes', 'kind': 'text'}, {'key': 'lower', 'label': 'If lower', 'kind': 'text'},
                    {'key': 'higher', 'label': 'If higher', 'kind': 'text'}, {'key': 'at_lower', 'label': 'Result if lower', 'kind': 'money'},
                    {'key': 'at_higher', 'label': 'Result if higher', 'kind': 'money'}, {'key': 'swing', 'label': 'Swing', 'kind': 'money'}],
        'rows': [[x['label'], show(x['kind'], x['lo']), show(x['kind'], x['hi']), _m(x['lo_final']), _m(x['hi_final']), _m(x['swing'])] for x in rows],
    }
    bars = [{'label': x['label'], 'lower_value': show(x['kind'], x['lo']), 'higher_value': show(x['kind'], x['hi']),
             'lower_delta': _m(x['lo_delta']), 'higher_delta': _m(x['hi_delta']), 'swing': _m(x['swing'])} for x in rows]
    interp = [
        'Under these assumptions the %s is %s. Each line below changes one thing and keeps everything else the same.' % (metric.lower(), kes(base_val)),
        '%s matters most here: testing %s against %s moves the result from %s to %s.'
        % (top['label'], show(top['kind'], top['lo']), show(top['kind'], top['hi']), kes(top['lo_final']), kes(top['hi_final'])),
    ]
    if len(rows) > 1:
        second = rows[1]
        interp.append('%s comes next, with a swing of %s.' % (second['label'], kes(second['swing'])))
        interp.append('%s has the smallest effect of the things tested (%s).' % (rows[-1]['label'], kes(rows[-1]['swing'])))
    warnings = [{'code': 'one_at_a_time', 'message': 'Each factor is changed on its own. In real life several change at once, and some move together.'},
                {'code': 'examples', 'message': 'The steps are examples to show what matters, not forecasts of what will happen.'}]
    extra = [_assume('Test steps', 'Each factor is moved down and up by: ' + '; '.join('%s by %s' % (x['label'].lower(), x['step']) for x in rows), 'assumption')]
    headline = {'label': 'Matters most: ' + top['label'].lower(), 'value': kes(top['swing']),
                'caption': 'Swing in the %s between the lower and higher case' % metric.lower()}
    methodology = [
        'Model sensitivity version %s, built on the compound-projection engine.' % MODEL_VERSION,
        'The base case is calculated, then each factor is run again with one value lowered and raised, everything else unchanged.',
        'Factors are ranked by the gap between their lower and higher results (the swing).',
    ]
    return _finish('sensitivity', date.today(), copy.deepcopy(raw), headline, [], table, None, warnings,
                   _base_assumptions(base, extra), methodology, interp, []) | {'bars': bars, 'base_value': _m(base_val), 'measure': metric}


# ================================================================= stress tests
def stress(raw):
    d, _plain_base = _check(raw)
    # Always measure in today's money too, so inflation shocks show up.
    raw2 = apply_overrides(raw, {'include_inflation': True})
    d2 = normalize(raw2)
    base = project(d2)
    real_on = d2['inflation'] > 0
    base_nominal = D(base['summary']['final_balance'])
    base_real = _final(base, True)
    years = d['years']

    scenarios = []

    def add(name, what, overrides):
        try:
            res = project(normalize(apply_overrides(raw2, overrides)))
        except EngineError:
            return
        scenarios.append({'name': name, 'what': what, 'res': res})

    r = d['annual_return']
    add('Lower returns', 'Yearly return 3 percentage points lower for the whole time.', {'annual_return': _text(_clamp(r - 3, D(-50), D(100)))})
    add('Higher inflation', 'Inflation 4 percentage points higher for the whole time.', {'inflation': _text(_clamp(d2['inflation'] + 4, D(-10), D(100)))})

    mid = int(years // 2)
    if years >= 2 and mid >= 1:
        points = {p['month']: D(p['closing']) for p in base['series']}
        at = points.get(mid * 12) or points.get(min(points, key=lambda m: abs(m - mid * 12)))
        loss = -(at * D('0.30')).quantize(D('0.01'), rounding=ROUND_HALF_UP)
        lumps = [{'year': _text(y), 'amount': _text(a)} for y, a in d2['lump_sums']] + [{'year': str(mid), 'amount': _text(loss)}]
        add('A bad year in the middle', 'A one-off loss of 30%% of the balance in year %d, then normal growth.' % mid, {'lump_sums': lumps})

    if d['contribution'] > 0 and years >= 4:
        start = int(years // 2)
        pauses = [{'from_year': _text(a), 'to_year': _text(b)} for a, b in d2['pauses']] + [{'from_year': str(start), 'to_year': str(start + 2)}]
        add('Two years without saving', 'You cannot save for 2 years, from year %d to year %d.' % (start, start + 2), {'pauses': pauses})

    add('Higher fees', 'Yearly fee 1 percentage point higher.', {'include_fees': True, 'annual_fee': _text(_clamp(d2['annual_fee'] + 1, ZERO, D(20)))})

    combo = {'annual_return': _text(_clamp(r - 3, D(-50), D(100))), 'inflation': _text(_clamp(d2['inflation'] + 4, D(-10), D(100)))}
    if d['contribution'] > 0 and years >= 4:
        start = int(years // 2)
        combo['pauses'] = [{'from_year': _text(a), 'to_year': _text(b)} for a, b in d2['pauses']] + [{'from_year': str(start), 'to_year': str(start + 2)}]
    add('Several things go wrong', 'Lower returns, higher inflation' + (' and two years without saving' if 'pauses' in combo else '') + ' together.', combo)

    if not scenarios:
        raise EngineError([{'field': 'inputs', 'message': 'There is nothing to stress yet. Fill in the calculator first.'}])

    def target_line(res):
        s = res['summary']
        if d['target'] is None:
            return ''
        return 'Target reached in month %d' % s['target_month'] if s['target_month'] is not None else 'Target not reached'

    rows = []
    base_row = ['Base case', 'Your assumptions as entered.', _m(base_nominal), _m(base_real), _m(ZERO), target_line(base)]
    rows.append(base_row)
    worst = None
    for sc in scenarios:
        s = sc['res']['summary']
        nominal, real = D(s['final_balance']), _final(sc['res'], True)
        sc['delta_real'] = real - base_real
        sc['delta_nominal'] = nominal - base_nominal
        rows.append([sc['name'], sc['what'], _m(nominal), _m(real), _m(real - base_real), target_line(sc['res'])])
        if worst is None or sc['delta_real'] < worst['delta_real']:
            worst = sc
    columns = [{'key': 'scenario', 'label': 'Stress test', 'kind': 'text'}, {'key': 'what', 'label': 'What changes', 'kind': 'text'},
               {'key': 'final', 'label': 'Final balance', 'kind': 'money'}, {'key': 'real', 'label': "In today's money", 'kind': 'money'},
               {'key': 'change', 'label': "Change in today's money", 'kind': 'money'}, {'key': 'target', 'label': 'Target', 'kind': 'text'}]
    if d['target'] is None:
        columns.pop()
        rows = [r_[:-1] for r_ in rows]

    chart_pick = [s for s in scenarios if s['name'] in ('Lower returns', 'A bad year in the middle', 'Several things go wrong')][:3]
    pts = base['series']
    chart = {'title': 'Balance in the base case and under stress', 'x_label': 'Year', 'y_label': 'Balance', 'unit': 'KES',
             'x': [('%d' % (p['month'] // 12)) if p['month'] % 12 == 0 else ('%.1f' % (p['month'] / 12)) for p in pts],
             'series': [{'key': 'base', 'name': 'Base case', 'values': [p['closing'] for p in pts]}] +
                       [{'key': 's%d' % i, 'name': c['name'], 'values': [p['closing'] for p in c['res']['series']]} for i, c in enumerate(chart_pick)]}
    interp = ['Under your assumptions the final balance is %s (%s in today\'s money).' % (kes(base_nominal), kes(base_real))]
    interp.append('The hardest test here is "%s". It leaves %s in today\'s money, %s %s than the base case.'
                  % (worst['name'].lower(), kes(_final(worst['res'], True)), kes(abs(worst['delta_real'])), 'less' if worst['delta_real'] < 0 else 'more'))
    broke = [s for s in scenarios if s['res']['summary']['depletion_month'] is not None]
    if broke:
        interp.append('In %s the money would run out.' % ' and '.join('"' + b['name'].lower() + '"' for b in broke))
    if d['target'] is not None:
        missed = [s['name'] for s in scenarios if s['res']['summary']['target_month'] is None]
        if missed and base['summary']['target_month'] is not None:
            interp.append('Your target would be missed under: ' + ', '.join(m.lower() for m in missed) + '.')
        elif not missed:
            interp.append('Your target is still reached in every test.')
    warnings = [{'code': 'examples', 'message': 'These shocks are examples, not forecasts. Real downturns can be larger, smaller or last longer.'}]
    if not real_on:
        warnings.append({'code': 'no_inflation', 'message': 'You have not entered an inflation rate, so "today\'s money" equals the nominal balance except in the inflation test.'})
    extra = [_assume('Lower returns', '3 percentage points lower a year', 'assumption'), _assume('Higher inflation', '4 percentage points higher a year', 'assumption')]
    if any(s['name'] == 'A bad year in the middle' for s in scenarios):
        extra.append(_assume('Bad year', 'A 30% loss in the middle year', 'assumption'))
    if any(s['name'] == 'Two years without saving' for s in scenarios):
        extra.append(_assume('Pause', 'Two years without saving in the middle', 'assumption'))
    extra.append(_assume('Higher fees', '1 percentage point higher a year', 'assumption'))
    headline = {'label': 'Hardest test: ' + worst['name'].lower(), 'value': kes(_final(worst['res'], True)),
                'caption': "In today's money, compared with %s in the base case" % kes(base_real)}
    methodology = [
        'Model stress version %s, built on the compound-projection engine.' % MODEL_VERSION,
        'The base case and each shock are calculated with the same engine. Results are compared in today\'s money so inflation shows up.',
        'The mid-term loss is 30% of the base-case balance at that year, applied as a one-off withdrawal.',
    ]
    return _finish('stress', date.today(), copy.deepcopy(raw), headline, [], {'title': 'Stress tests', 'columns': columns, 'rows': rows}, chart,
                   warnings, _base_assumptions(base, extra), methodology, interp, [])


# ================================================================= comparing places to put the same money
OPTION_KINDS = {'tbill': 'Treasury bill', 'mmf': 'Money market fund', 'sacco': 'SACCO', 'bank': 'Bank savings account'}
RULE_FOR = {'tbill': 'wht_tbill', 'mmf': 'wht_mmf', 'sacco': 'wht_dividend_resident', 'bank': 'wht_bank_interest'}
RISK_NOTE = {
    'tbill': 'Treasury bill: the yield is fixed when you buy. Rolling over assumes the same yield every time, which auctions do not promise.',
    'mmf': 'Money market fund: the yield changes daily and is not guaranteed.',
    'sacco': 'SACCO: the dividend is set each year at the annual meeting and is not promised. Deposits may be hard to withdraw.',
    'bank': 'Bank savings account: the rate can change, and some accounts have fees or limits.',
}


def _metric_raw(result, key):
    return D(next(m for m in result['metrics'] if m['key'] == key)['raw'])


def _option_values(kind, opt, amount, years, exempt):
    """(yearly values from 0 to years, rule data used) for one option, running the same models as the single calculators."""
    if kind == 'tbill':
        r = tbill({'amount': amount, 'amount_is': 'cost', 'tenor_days': opt.get('tenor_days') or 364, 'yield_pct': opt.get('yield_pct'), 'tax_exempt': exempt})
        rate = _metric_raw(r, 'net_annual_return') / 100
        return [amount * (1 + rate) ** t for t in range(years + 1)]
    if kind in ('mmf', 'bank'):
        raw = {'initial': amount, 'years': years, 'yield_pct': opt.get('yield_pct'), 'yield_basis': opt.get('yield_basis') or 'gross', 'tax_exempt': exempt}
        if kind == 'bank' and not exempt:
            raw['tax_rate'] = kenya_rules.rule('wht_bank_interest')['rate']
        r = mmf(raw)
        return [amount] + [D(row[5]) for row in r['table']['rows']]
    r = sacco({'initial': amount, 'years': years, 'dividend_pct': opt.get('yield_pct'), 'payout': 'reinvest', 'tax_exempt': exempt})
    return [amount] + [D(row[7]) for row in r['table']['rows']]


def compare(raw):
    from datetime import date as _date
    errors = []
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    amount = _dec(raw.get('amount'), 'amount', errors, 1, 10 ** 11, None, required=True)
    years = _int(raw.get('years'), 'years', errors, 1, 30, None, required=True)
    exempt = bool(raw.get('tax_exempt'))
    opts = raw.get('options')
    if not isinstance(opts, list) or not 2 <= len(opts) <= 5:
        errors.append({'field': 'options', 'message': 'Choose 2 to 5 things to compare.'})
        opts = []
    if errors:
        raise EngineError(errors)

    results, used_rules, names = [], [], {}
    for i, opt in enumerate(opts):
        if not isinstance(opt, dict) or opt.get('kind') not in OPTION_KINDS:
            errors.append({'field': 'options[%d].kind' % i, 'message': 'Choose Treasury bill, money market fund, SACCO or bank account.'})
            continue
        kind = opt['kind']
        base_name = (str(opt.get('name') or '').strip() or OPTION_KINDS[kind])[:40]
        names[base_name] = names.get(base_name, 0) + 1
        name = base_name if names[base_name] == 1 else '%s %d' % (base_name, names[base_name])
        try:
            values = _option_values(kind, opt, amount, years, exempt)
            free = _option_values(kind, opt, amount, years, True)
        except EngineError as exc:
            for e in exc.errors:
                key = {'dividend_pct': 'yield_pct'}.get(e['field'], e['field'])
                errors.append({'field': 'options[%d].%s' % (i, key), 'message': e['message']})
            continue
        final, free_final = values[-1], free[-1]
        rule_data = kenya_rules.rule(RULE_FOR[kind])
        used_rules.append(rule_data)
        results.append({'name': name, 'kind': kind, 'opt': opt, 'values': values, 'final': final, 'lost': free_final - final,
                        'annual': (final / amount) ** (D(1) / D(years)) - 1, 'rule': rule_data})
    if errors:
        raise EngineError(errors)

    results.sort(key=lambda x: x['final'], reverse=True)
    best, worst = results[0], results[-1]

    def what(x):
        o, k = x['opt'], x['kind']
        yv = _pp(D(str(o.get('yield_pct'))))
        if k == 'tbill':
            return '%s-day bill at %s, bought again each time it matures' % (o.get('tenor_days') or 364, yv)
        if k == 'sacco':
            return '%s dividend a year, added to deposits' % yv
        basis = 'before tax' if (o.get('yield_basis') or 'gross') == 'gross' else 'after tax'
        return '%s a year, %s' % (yv, basis)

    columns = [{'key': 'option', 'label': 'Option', 'kind': 'text'}, {'key': 'what', 'label': 'Assumes', 'kind': 'text'},
               {'key': 'final', 'label': 'Value at the end', 'kind': 'money'}, {'key': 'gain', 'label': 'Gain after tax', 'kind': 'money'},
               {'key': 'annual', 'label': 'Yearly return after tax', 'kind': 'text'}, {'key': 'lost', 'label': 'Growth lost to tax', 'kind': 'money'}]
    rows = [[x['name'], what(x), _m(x['final']), _m(x['final'] - amount), pct(x['annual'] * 100), _m(x['lost'])] for x in results]
    chart = {'title': 'Value over time', 'x_label': 'Year', 'y_label': 'Value', 'unit': 'KES', 'x': [str(t) for t in range(years + 1)],
             'series': [{'key': 'o%d' % i, 'name': x['name'], 'values': [_m(v) for v in x['values']]} for i, x in enumerate(results)]}
    gap = best['final'] - worst['final']
    interp = [
        'Putting %s in each for %s, %s ends highest at %s and %s lowest at %s, a gap of %s.'
        % (kes(amount), _years(years), best['name'], kes(best['final']), worst['name'], kes(worst['final']), kes(gap)),
        'After tax, the yearly returns range from %s to %s.' % (pct(worst['annual'] * 100), pct(best['annual'] * 100)),
        'These numbers do not show risk, how quickly you can get your money back, or costs such as exit fees. A higher number here is not automatically a better choice.',
    ]
    warnings = [{'code': 'numbers_only', 'message': 'This ranks numbers under the yields you entered. It says nothing about safety or access to your money.'}]
    for kind in dict.fromkeys(x['kind'] for x in results):
        warnings.append({'code': 'risk_' + kind, 'message': RISK_NOTE[kind]})
    assumptions = [_assume('Amount', kes(amount), 'user-entered'), _assume('Time', _years(years), 'user-entered')]
    for x in results:
        assumptions.append(_assume(x['name'], what(x), 'assumption'))
        if exempt:
            assumptions.append(_assume('Tax on ' + x['name'], '0% (you said you are tax exempt)', 'user-entered'))
        else:
            assumptions.append(_assume('Tax on ' + x['name'], x['rule']['rate'] + '%', 'sourced', x['rule']))
    methodology = [
        'Model compare version %s, running the same models as the single calculators on the same amount and time.' % MODEL_VERSION,
        'Each option is calculated with its own tax rule, then shown as the value at the end, the gain, and the yearly return after tax.',
        '"Growth lost to tax" is the difference between the result with tax and the result for a tax-exempt investor.',
    ]
    headline = {'label': 'Highest result: ' + best['name'], 'value': kes(best['final']),
                'caption': 'Gain after tax %s over %s. Compares numbers only.' % (kes(best['final'] - amount), _years(years))}
    inputs = copy.deepcopy(raw)
    return _finish('compare', _date.today(), inputs, headline, [], {'title': 'Side by side', 'columns': columns, 'rows': rows}, chart,
                   warnings, assumptions, methodology, interp, used_rules)
