"""The Financial Notepad calculation engine: deterministic, Decimal-based, no Django.

One model, `compound-projection`, covers savings with recurring contributions, one-off deposits and withdrawals,
several withdrawal methods, fees, tax on growth and inflation. Every result has the same shape (the "result
contract"), so graphs, tables, metric cards and scenario comparisons are all views of ONE calculation.

Conventions (also returned in every result, so a saved note can always explain itself):
  * Time moves in whole months. `years` is converted to months (rounded).
  * The stated return is turned into an equivalent MONTHLY rate from the chosen compounding convention
    (nominal rate compounded daily/monthly/quarterly/semiannually/annually, or an effective annual rate).
  * In each month, in this order: start-of-month deposits, growth, tax on that growth, fee, end-of-month
    deposits, then withdrawals that fall due. Nothing is rounded until it is shown (2 decimal places).
  * Inflation only produces a second, "real" (today's money) view; it never changes the nominal balance,
    except for the "inflation_adjusted" withdrawal method which is defined in today's money.
Nothing here is a forecast: returns, inflation, fees and tax are assumptions the user supplies.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

MODEL_ID = 'compound-projection'
MODEL_VERSION = '1.0.0'
MAX_MONTHS = 80 * 12
CENT = Decimal('0.01')

PERIOD_MONTHS = {'monthly': 1, 'quarterly': 3, 'semiannual': 6, 'annually': 12}
COMPOUNDING = {'daily': 365, 'monthly': 12, 'quarterly': 4, 'semiannual': 2, 'annual': 1}
WITHDRAWAL_MODES = ('none', 'fixed', 'pct_start', 'pct_current', 'inflation_adjusted')
INPUT_LABELS = {
    'initial': 'Starting amount', 'years': 'Duration (years)', 'annual_return': 'Assumed annual return (%)',
    'rate_type': 'Rate type', 'compounding': 'Compounding', 'contribution': 'Contribution',
    'contribution_frequency': 'Contribution frequency', 'contribution_timing': 'Contribution timing',
    'annual_increase': 'Yearly increase in contribution (%)', 'contribution_start_year': 'Contributions start (year)',
    'contribution_end_year': 'Contributions stop (year)', 'annual_fee': 'Yearly fee (%)', 'tax_on_growth': 'Tax on growth (%)',
    'inflation': 'Assumed inflation (%)', 'target': 'Target balance', 'withdrawal.mode': 'Withdrawal method',
    'withdrawal.amount': 'Withdrawal amount', 'withdrawal.percent': 'Withdrawal (% a year)',
    'withdrawal.frequency': 'Withdrawal frequency', 'withdrawal.start_year': 'Withdrawals start (year)',
    'withdrawal.end_year': 'Withdrawals stop (year)', 'include_fees': 'Include fees', 'include_tax': 'Include tax',
    'include_inflation': 'Show inflation-adjusted view',
}


class EngineError(ValueError):
    """Invalid input. `errors` is a list of {'field', 'message'} so the app can mark the exact fields."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(f"{e['field']}: {e['message']}" for e in errors))


# ---------------------------------------------------------------- parsing and validation
def _dec(value, field, errors, low=None, high=None, default=None, required=False):
    if value is None or value == '':
        if required:
            errors.append({'field': field, 'message': 'This value is required.'})
        return default
    if isinstance(value, bool):
        errors.append({'field': field, 'message': 'Enter a number.'})
        return default
    try:
        number = Decimal(str(value).strip().replace(',', ''))
    except (InvalidOperation, ValueError):
        errors.append({'field': field, 'message': 'Enter a number.'})
        return default
    if not number.is_finite():
        errors.append({'field': field, 'message': 'Enter a number.'})
        return default
    if low is not None and number < Decimal(str(low)):
        errors.append({'field': field, 'message': f'Must be at least {low}.'})
        return default
    if high is not None and number > Decimal(str(high)):
        errors.append({'field': field, 'message': f'Must be at most {high}.'})
        return default
    return number


def _choice(value, field, errors, allowed, default):
    if value is None or value == '':
        return default
    if value not in allowed:
        errors.append({'field': field, 'message': 'Choose one of: ' + ', '.join(allowed) + '.'})
        return default
    return value


def _flag(value, default=True):
    return default if value is None else bool(value)


def normalize(raw):
    """Validate raw input (numbers or numeric strings) and return a clean dict of Decimals and choices."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    d = {}
    d['initial'] = _dec(raw.get('initial'), 'initial', errors, 0, 10 ** 12, Decimal(0))
    years = _dec(raw.get('years'), 'years', errors, Decimal('0.0834'), 80, None, required=True)
    d['years'] = years
    d['months'] = max(1, int((years * 12).to_integral_value(ROUND_HALF_UP))) if years is not None else None
    d['annual_return'] = _dec(raw.get('annual_return'), 'annual_return', errors, -50, 100, Decimal(0))
    d['rate_type'] = _choice(raw.get('rate_type'), 'rate_type', errors, ('nominal', 'effective'), 'nominal')
    d['compounding'] = _choice(raw.get('compounding'), 'compounding', errors, tuple(COMPOUNDING), 'monthly')
    d['contribution'] = _dec(raw.get('contribution'), 'contribution', errors, 0, 10 ** 10, Decimal(0))
    d['contribution_frequency'] = _choice(raw.get('contribution_frequency'), 'contribution_frequency', errors, tuple(PERIOD_MONTHS), 'monthly')
    d['contribution_timing'] = _choice(raw.get('contribution_timing'), 'contribution_timing', errors, ('start', 'end'), 'end')
    d['annual_increase'] = _dec(raw.get('annual_increase'), 'annual_increase', errors, -50, 100, Decimal(0))
    d['contribution_start_year'] = _dec(raw.get('contribution_start_year'), 'contribution_start_year', errors, 0, 80, Decimal(0))
    d['contribution_end_year'] = _dec(raw.get('contribution_end_year'), 'contribution_end_year', errors, 0, 80, None)
    d['annual_fee'] = _dec(raw.get('annual_fee'), 'annual_fee', errors, 0, 20, Decimal(0))
    d['tax_on_growth'] = _dec(raw.get('tax_on_growth'), 'tax_on_growth', errors, 0, 60, Decimal(0))
    d['inflation'] = _dec(raw.get('inflation'), 'inflation', errors, -10, 100, Decimal(0))
    d['target'] = _dec(raw.get('target'), 'target', errors, 0, 10 ** 13, None)
    d['include_fees'] = _flag(raw.get('include_fees'))
    d['include_tax'] = _flag(raw.get('include_tax'))
    d['include_inflation'] = _flag(raw.get('include_inflation'))
    d['currency'] = 'KES'

    start = raw.get('start_date')
    d['start_date'] = None
    if start not in (None, ''):
        try:
            d['start_date'] = date.fromisoformat(str(start)[:10])
        except ValueError:
            errors.append({'field': 'start_date', 'message': 'Use a date like 2026-01-31.'})

    w = raw.get('withdrawal') or {}
    if not isinstance(w, dict):
        errors.append({'field': 'withdrawal', 'message': 'Withdrawal settings must be an object.'})
        w = {}
    mode = _choice(w.get('mode'), 'withdrawal.mode', errors, WITHDRAWAL_MODES, 'none')
    wd = {'mode': mode}
    wd['frequency'] = _choice(w.get('frequency'), 'withdrawal.frequency', errors, tuple(PERIOD_MONTHS), 'monthly')
    wd['start_year'] = _dec(w.get('start_year'), 'withdrawal.start_year', errors, 0, 80, Decimal(0))
    wd['end_year'] = _dec(w.get('end_year'), 'withdrawal.end_year', errors, 0, 80, None)
    wd['amount'] = _dec(w.get('amount'), 'withdrawal.amount', errors, 0, 10 ** 10, Decimal(0))
    wd['percent'] = _dec(w.get('percent'), 'withdrawal.percent', errors, 0, 100, Decimal(0))
    if mode in ('fixed', 'inflation_adjusted') and not wd['amount']:
        errors.append({'field': 'withdrawal.amount', 'message': 'Enter the amount to withdraw each period.'})
    if mode in ('pct_start', 'pct_current') and not wd['percent']:
        errors.append({'field': 'withdrawal.percent', 'message': 'Enter the percentage to withdraw each year.'})
    d['withdrawal'] = wd

    pauses = []
    for i, item in enumerate(raw.get('pauses') or []):
        if not isinstance(item, dict):
            errors.append({'field': f'pauses[{i}]', 'message': 'Each pause needs from_year and to_year.'})
            continue
        a = _dec(item.get('from_year'), f'pauses[{i}].from_year', errors, 0, 80, None, required=True)
        b = _dec(item.get('to_year'), f'pauses[{i}].to_year', errors, 0, 80, None, required=True)
        if a is not None and b is not None:
            if b <= a:
                errors.append({'field': f'pauses[{i}]', 'message': 'A pause must end after it starts.'})
            else:
                pauses.append((a, b))
    d['pauses'] = pauses

    lumps = []
    for i, item in enumerate(raw.get('lump_sums') or []):
        if not isinstance(item, dict):
            errors.append({'field': f'lump_sums[{i}]', 'message': 'Each one-off needs year and amount.'})
            continue
        y = _dec(item.get('year'), f'lump_sums[{i}].year', errors, 0, 80, None, required=True)
        amt = _dec(item.get('amount'), f'lump_sums[{i}].amount', errors, -(10 ** 12), 10 ** 12, None, required=True)
        if y is not None and amt is not None:
            lumps.append((y, amt))
    if len(lumps) > 60:
        errors.append({'field': 'lump_sums', 'message': 'At most 60 one-off amounts.'})
    d['lump_sums'] = lumps

    if d['contribution_end_year'] is not None and d['contribution_end_year'] <= d['contribution_start_year']:
        errors.append({'field': 'contribution_end_year', 'message': 'Contributions must stop after they start.'})
    if errors:
        raise EngineError(errors)
    return d


def _plain(value):
    """Decimal to a JSON-friendly string without trailing noise."""
    if isinstance(value, Decimal):
        text = format(value.normalize(), 'f')
        return text if text != '-0' else '0'
    return value


def echo_inputs(d):
    """The validated inputs, as plain JSON, for the result contract."""
    out = {k: _plain(v) for k, v in d.items() if k not in ('months', 'pauses', 'lump_sums', 'withdrawal', 'start_date')}
    out['months'] = d['months']
    out['start_date'] = d['start_date'].isoformat() if d['start_date'] else None
    out['withdrawal'] = {k: _plain(v) for k, v in d['withdrawal'].items()}
    out['pauses'] = [{'from_year': _plain(a), 'to_year': _plain(b)} for a, b in d['pauses']]
    out['lump_sums'] = [{'year': _plain(y), 'amount': _plain(a)} for y, a in d['lump_sums']]
    return out


# ---------------------------------------------------------------- the projection
def monthly_rate(annual_return, rate_type, compounding):
    """Equivalent monthly growth rate as a Decimal fraction (0.01 means 1% a month)."""
    r = annual_return / 100
    if rate_type == 'effective':
        effective = r
    else:
        n = COMPOUNDING[compounding]
        effective = (1 + r / n) ** n - 1
    if effective == 0:
        return Decimal(0)
    return (1 + effective) ** (Decimal(1) / 12) - 1


def _add_months(day, months):
    index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    last = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return date(year, month, min(day.day, last))


def _money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _m(value):
    return format(_money(value), 'f')


def project(d, detail=False):
    """Run the model on normalised inputs `d` and return the full result contract."""
    with localcontext() as ctx:
        ctx.prec = 60
        return _project(d, detail)


def _due(month, length, start_month, timing):
    """Is a recurring cash flow due in this (1-based) month? Periods are counted from `start_month`."""
    if timing == 'start':
        return month > start_month and (month - start_month - 1) % length == 0
    return month > start_month and (month - start_month) % length == 0


def _project(d, detail):
    months = d['months']
    rate = monthly_rate(d['annual_return'], d['rate_type'], d['compounding'])
    fee_m = d['annual_fee'] / 100 / 12 if d['include_fees'] else Decimal(0)
    tax = d['tax_on_growth'] / 100 if d['include_tax'] else Decimal(0)
    infl = d['inflation'] / 100
    show_real = d['include_inflation'] and infl != 0

    c_len = PERIOD_MONTHS[d['contribution_frequency']]
    c_start = int((d['contribution_start_year'] * 12).to_integral_value(ROUND_HALF_UP))
    c_end = (int((d['contribution_end_year'] * 12).to_integral_value(ROUND_HALF_UP))
             if d['contribution_end_year'] is not None else None)
    pauses = [(int((a * 12).to_integral_value(ROUND_HALF_UP)), int((b * 12).to_integral_value(ROUND_HALF_UP))) for a, b in d['pauses']]
    lumps = {}
    for y, amt in d['lump_sums']:
        m = max(1, int((y * 12).to_integral_value(ROUND_HALF_UP)))
        if m <= months:
            lumps[m] = lumps.get(m, Decimal(0)) + amt

    w = d['withdrawal']
    w_mode = w['mode']
    w_len = PERIOD_MONTHS[w['frequency']]
    w_start = int((w['start_year'] * 12).to_integral_value(ROUND_HALF_UP))
    w_end = int((w['end_year'] * 12).to_integral_value(ROUND_HALF_UP)) if w['end_year'] is not None else None
    per_year = Decimal(12) / w_len

    balance = d['initial']
    cum = {'contrib': d['initial'], 'interest': Decimal(0), 'tax': Decimal(0), 'fees': Decimal(0), 'withdrawn': Decimal(0)}
    year_acc = {'contrib': Decimal(0), 'interest': Decimal(0), 'tax': Decimal(0), 'fees': Decimal(0), 'withdrawn': Decimal(0)}
    year_open = balance
    base_at_start = d['initial'] if w_start == 0 else None
    depleted_month = None
    shortfall_total = Decimal(0)
    target_month = 0 if (d['target'] is not None and balance >= d['target']) else None
    events = []
    annual, monthly_rows = [], []
    warnings = []

    def real(value, m):
        return value / ((1 + infl) ** (Decimal(m) / 12)) if show_real else value

    for m in range(1, months + 1):
        year_index = (m - 1) // 12
        contribution = Decimal(0)
        due = (d['contribution'] != 0 and _due(m, c_len, c_start, d['contribution_timing'])
               and (c_end is None or m <= c_end) and not any(a < m <= b for a, b in pauses))
        if due:
            contribution = d['contribution'] * ((1 + d['annual_increase'] / 100) ** year_index)
        start_in = Decimal(0)
        lump = lumps.get(m, Decimal(0))
        if d['contribution_timing'] == 'start':
            start_in += contribution
        if lump > 0:
            start_in += lump
        balance += start_in
        year_acc['contrib'] += (contribution if d['contribution_timing'] == 'start' else Decimal(0)) + (lump if lump > 0 else Decimal(0))
        cum['contrib'] += (contribution if d['contribution_timing'] == 'start' else Decimal(0)) + (lump if lump > 0 else Decimal(0))

        growth = balance * rate
        tax_paid = growth * tax if growth > 0 else Decimal(0)
        balance += growth - tax_paid
        fee = balance * fee_m
        balance -= fee
        year_acc['interest'] += growth
        year_acc['tax'] += tax_paid
        year_acc['fees'] += fee
        cum['interest'] += growth
        cum['tax'] += tax_paid
        cum['fees'] += fee

        if d['contribution_timing'] == 'end' and contribution:
            balance += contribution
            year_acc['contrib'] += contribution
            cum['contrib'] += contribution

        requested = Decimal(0)
        if lump < 0:
            requested += -lump
        if w_mode != 'none' and _due(m, w_len, w_start, 'end') and (w_end is None or m <= w_end):
            if w_mode == 'fixed':
                requested += w['amount']
            elif w_mode == 'inflation_adjusted':
                requested += w['amount'] * ((1 + infl) ** Decimal((m - 1) // 12))
            elif w_mode == 'pct_start':
                base = base_at_start if base_at_start is not None else balance
                requested += base * w['percent'] / 100 / per_year
            elif w_mode == 'pct_current':
                requested += balance * w['percent'] / 100 / per_year
        if requested > 0:
            paid = requested if requested <= balance else balance
            if requested - paid > Decimal('0.005'):
                shortfall_total += requested - paid
                if depleted_month is None:
                    depleted_month = m
                    events.append({'month': m, 'kind': 'depleted', 'label': 'The balance cannot cover a withdrawal.'})
            balance -= paid
            year_acc['withdrawn'] += paid
            cum['withdrawn'] += paid
        if lump:
            events.append({'month': m, 'kind': 'one_off', 'label': ('One-off deposit' if lump > 0 else 'One-off withdrawal'), 'amount': _m(lump)})
        if w_start == m:
            base_at_start = balance
        if target_month is None and d['target'] is not None and balance >= d['target']:
            target_month = m
            events.append({'month': m, 'kind': 'target', 'label': 'Target balance reached.'})

        if detail:
            row = {'month': m, 'balance': _m(balance), 'real_balance': _m(real(balance, m)),
                   'contributions': _m(cum['contrib']), 'withdrawn': _m(cum['withdrawn'])}
            if d['start_date']:
                row['date'] = _add_months(d['start_date'], m).isoformat()
            monthly_rows.append(row)
        if m % 12 == 0 or m == months:
            annual.append({
                'year': _plain((Decimal(m) / 12).quantize(Decimal('0.01'))), 'month': m,
                'opening': _m(year_open), 'contributions': _m(year_acc['contrib']), 'growth': _m(year_acc['interest']),
                'tax': _m(year_acc['tax']), 'fees': _m(year_acc['fees']), 'withdrawals': _m(year_acc['withdrawn']),
                'closing': _m(balance), 'real_closing': _m(real(balance, m)),
                'total_contributed': _m(cum['contrib']), 'total_growth': _m(cum['interest'] - cum['tax'] - cum['fees']),
                'total_withdrawn': _m(cum['withdrawn']),
            })
            if d['start_date']:
                annual[-1]['date'] = _add_months(d['start_date'], m).isoformat()
            year_open = balance
            year_acc = {k: Decimal(0) for k in year_acc}

    final = balance
    growth_net = cum['interest'] - cum['tax'] - cum['fees']
    start_row = {'year': '0', 'month': 0, 'closing': _m(d['initial']), 'real_closing': _m(d['initial']),
                 'total_contributed': _m(d['initial']), 'total_growth': '0.00', 'total_withdrawn': '0.00'}
    series = [start_row] + [{k: row[k] for k in ('year', 'month', 'closing', 'real_closing', 'total_contributed', 'total_growth', 'total_withdrawn')} for row in annual]
    effective = (1 + rate) ** 12 - 1 if rate != 0 else Decimal(0)

    if depleted_month is not None:
        warnings.append({'code': 'depleted', 'message': 'Under these assumptions the balance runs out in month %d (year %s); withdrawals after that could not be paid in full.' % (depleted_month, _plain((Decimal(depleted_month) / 12).quantize(Decimal('0.1')))), 'month': depleted_month})
    if w_mode == 'inflation_adjusted' and infl == 0:
        warnings.append({'code': 'no_inflation', 'message': 'Inflation is 0%, so inflation-adjusted withdrawals stay the same each year.'})
    if d['target'] is not None and target_month is None:
        warnings.append({'code': 'target_missed', 'message': 'The target balance is not reached within this time under these assumptions.'})
    if d['annual_return'] < 0:
        warnings.append({'code': 'negative_return', 'message': 'A negative return means the balance shrinks before contributions.'})
    if shortfall_total > 0:
        warnings.append({'code': 'shortfall', 'message': 'Withdrawals that could not be paid: KES %s in total.' % _m(shortfall_total)})

    summary = {
        'final_balance': _m(final),
        'final_real_balance': _m(real(final, months)) if show_real else None,
        'total_contributed': _m(cum['contrib']),
        'total_withdrawn': _m(cum['withdrawn']),
        'total_growth': _m(cum['interest']),
        'total_tax': _m(cum['tax']),
        'total_fees': _m(cum['fees']),
        'net_growth': _m(growth_net),
        'growth_share': _plain(((growth_net / final) * 100).quantize(Decimal('0.1'))) if final > 0 else None,
        'monthly_rate': _plain(rate.quantize(Decimal('0.0000000001'))),
        'effective_annual_rate': _plain((effective * 100).quantize(Decimal('0.0001'))),
        'depletion_month': depleted_month,
        'target_month': target_month,
        'months': months,
    }
    result = {
        'model': MODEL_ID, 'version': MODEL_VERSION,
        'inputs': echo_inputs(d),
        'conventions': {
            'currency': 'KES', 'rounding': 'Calculated unrounded; shown to 2 decimal places (half up).',
            'time_step': 'Monthly', 'rate_conversion': 'Equivalent monthly rate from the stated rate and compounding.',
            'order_in_month': 'Start deposits, growth, tax on growth, fee, end deposits, withdrawals.',
        },
        'summary': summary, 'annual': annual, 'series': series, 'events': events, 'warnings': warnings,
        'assumptions': assumptions_of(d),
        'methodology': methodology_of(d),
    }
    if detail:
        result['monthly'] = monthly_rows
    result['interpretation'] = interpret(result)
    return result


# ---------------------------------------------------------------- words that come from the numbers
def assumptions_of(d):
    items = [
        {'label': 'Starting amount', 'value': 'KES ' + _commas(d['initial']), 'kind': 'user-entered'},
        {'label': 'Duration', 'value': _plain(d['years']) + ' years', 'kind': 'user-entered'},
        {'label': 'Annual return', 'value': _plain(d['annual_return']) + '% (' + ('effective' if d['rate_type'] == 'effective' else 'nominal, compounded ' + d['compounding']) + ')', 'kind': 'assumption'},
    ]
    if d['contribution']:
        items.append({'label': 'Contribution', 'value': 'KES %s %s, paid at the %s of each period%s' % (
            _commas(d['contribution']), d['contribution_frequency'], d['contribution_timing'],
            (', rising %s%% a year' % _plain(d['annual_increase'])) if d['annual_increase'] else ''), 'kind': 'user-entered'})
    w = d['withdrawal']
    if w['mode'] != 'none':
        text = {'fixed': 'KES %s %s' % (_commas(w['amount']), w['frequency']),
                'inflation_adjusted': 'KES %s %s in today\'s money, rising with inflation' % (_commas(w['amount']), w['frequency']),
                'pct_start': '%s%% a year of the balance when withdrawals begin' % _plain(w['percent']),
                'pct_current': '%s%% a year of the current balance' % _plain(w['percent'])}[w['mode']]
        items.append({'label': 'Withdrawals', 'value': text + ', from year ' + _plain(w['start_year']), 'kind': 'user-entered'})
    if d['annual_fee'] and d['include_fees']:
        items.append({'label': 'Fees', 'value': _plain(d['annual_fee']) + '% a year of the balance', 'kind': 'assumption'})
    if d['tax_on_growth'] and d['include_tax']:
        items.append({'label': 'Tax on growth', 'value': _plain(d['tax_on_growth']) + '% (entered by you; not checked against current tax rules)', 'kind': 'assumption'})
    if d['inflation'] and d['include_inflation']:
        items.append({'label': 'Inflation', 'value': _plain(d['inflation']) + '% a year', 'kind': 'assumption'})
    if d['target'] is not None:
        items.append({'label': 'Target balance', 'value': 'KES ' + _commas(d['target']), 'kind': 'user-entered'})
    return items


def methodology_of(d):
    lines = [
        'Model %s version %s.' % (MODEL_ID, MODEL_VERSION),
        'The stated return is converted to an equivalent monthly rate, and the balance is updated month by month.',
        'Each month: deposits made at the start, growth, tax on that growth, the fee on the balance, deposits made at the end, then any withdrawal that is due.',
        'Amounts are not rounded while calculating; they are shown to 2 decimal places.',
        'Returns, inflation, fees and tax are assumptions you chose. They are not predictions or guarantees.',
    ]
    w = d['withdrawal']
    if w['mode'] == 'inflation_adjusted':
        lines.append('Inflation-adjusted withdrawals are defined in today\'s money and grow with the assumed inflation each year from the start of the model.')
    if w['mode'] == 'pct_start':
        lines.append('The percentage is applied to the balance on the day withdrawals begin and then stays the same amount.')
    if w['mode'] == 'pct_current':
        lines.append('The percentage is applied to the balance at each withdrawal date, so withdrawals shrink when the balance shrinks.')
    if d['inflation'] and d['include_inflation']:
        lines.append('The inflation-adjusted view divides each balance by (1 + inflation) for the years elapsed.')
    return lines


def _commas(value):
    return format(_money(Decimal(value)), ',.2f').replace('.00', '')


def interpret(result):
    """Plain sentences built only from the numbers in `result`. They describe; they never advise or promise."""
    i, s = result['inputs'], result['summary']
    out = []
    years = i['years']
    head = 'Under these assumptions, over %s years' % years
    parts = []
    if Decimal(i['initial']) > 0:
        parts.append('starting with KES %s' % _commas(i['initial']))
    if Decimal(i['contribution']) > 0:
        parts.append('adding KES %s %s' % (_commas(i['contribution']), i['contribution_frequency']))
    if parts:
        head += ', ' + ' and '.join(parts)
    head += ', the balance is projected to reach KES %s' % _commas(s['final_balance'])
    if s['final_real_balance'] is not None:
        head += ' (about KES %s in today\'s money)' % _commas(s['final_real_balance'])
    out.append(head + '.')
    contributed, growth = Decimal(s['total_contributed']), Decimal(s['net_growth'])
    if contributed > 0 or growth != 0:
        out.append('Of the money put in (KES %s), the model shows KES %s of net growth after any tax and fees.' % (_commas(contributed), _commas(growth)))
    if Decimal(s['total_withdrawn']) > 0:
        out.append('KES %s is withdrawn along the way.' % _commas(s['total_withdrawn']))
    if s['depletion_month'] is not None:
        out.append('The balance runs out in month %d, so later withdrawals could not be paid in full.' % s['depletion_month'])
    elif s['target_month'] is not None:
        out.append('The target of KES %s is reached in month %d.' % (_commas(i['target']), s['target_month']))
    out.append('This is an illustration based on the assumptions listed, not a forecast or a recommendation.')
    return out


# ---------------------------------------------------------------- solving backwards
def _final(d):
    with localcontext() as ctx:
        ctx.prec = 60
        return _project(d, False)['summary']


def _with(d, **changes):
    new = dict(d)
    new.update(changes)
    return new


def _bisect(fn, low, high, goal_met, tolerance=Decimal('0.001'), steps=120):
    """Smallest x in [low, high] where goal_met(fn(x)) is true, assuming monotone behaviour."""
    for _ in range(steps):
        mid = (low + high) / 2
        if goal_met(fn(mid)):
            high = mid
        else:
            low = mid
        if high - low <= tolerance:
            break
    return high


def solve(d, kind, detail=False):
    """Solve for an unknown. Returns {'solution': {...}, 'result': contract} or {'no_solution': reason, 'result': ...}."""
    with localcontext() as ctx:
        ctx.prec = 60
        if kind == 'contribution_for_target':
            return _solve_contribution(d, detail)
        if kind == 'years_to_target':
            return _solve_years(d, detail)
        if kind == 'capital_for_withdrawal':
            return _solve_capital(d, detail)
        if kind == 'max_withdrawal':
            return _solve_max_withdrawal(d, detail)
    raise EngineError([{'field': 'solve.kind', 'message': 'Unknown solver.'}])


def _need_target(d):
    if d['target'] is None:
        raise EngineError([{'field': 'target', 'message': 'Enter the target balance to solve for.'}])


def _solve_contribution(d, detail):
    _need_target(d)
    target = d['target']
    base = _with(d, contribution=Decimal(0))
    if Decimal(_final(base)['final_balance']) >= target:
        result = _project(base, detail)
        return {'solution': {'kind': 'contribution_for_target', 'value': '0.00', 'explanation': 'The target is reached without any contribution.'}, 'result': result}
    high = max(Decimal(1), target / max(1, d['months']))
    ceiling = Decimal(10) ** 10
    while Decimal(_final(_with(d, contribution=high))['final_balance']) < target:
        high *= 2
        if high > ceiling:
            return {'no_solution': 'No contribution up to KES 10 billion a period reaches this target under these assumptions (for example because withdrawals or fees take it back).', 'result': _project(_with(d, contribution=ceiling), detail)}
    x = _bisect(lambda c: Decimal(_final(_with(d, contribution=c))['final_balance']), Decimal(0), high, lambda f: f >= target, Decimal('0.0001'))
    x = x.quantize(CENT, rounding=ROUND_HALF_UP)
    if Decimal(_final(_with(d, contribution=x))['final_balance']) < target:
        x += CENT
    result = _project(_with(d, contribution=x), detail)
    return {'solution': {'kind': 'contribution_for_target', 'value': _m(x), 'explanation': 'The smallest %s contribution (to the nearest cent) that reaches KES %s in %s years.' % (d['contribution_frequency'], _commas(target), _plain(d['years']))}, 'result': result}


def _solve_years(d, detail):
    _need_target(d)
    longest = _with(d, years=Decimal(80), months=MAX_MONTHS)
    run = _project(longest, False)
    month = run['summary']['target_month']
    if month is None:
        return {'no_solution': 'The target is not reached within 80 years under these assumptions. Increase the contribution or the return, or lower the target.', 'result': run}
    exact = _with(d, years=(Decimal(month) / 12), months=max(1, month))
    result = _project(exact, detail)
    return {'solution': {'kind': 'years_to_target', 'value': _plain((Decimal(month) / 12).quantize(Decimal('0.01'))), 'months': month,
                         'explanation': 'The target is first reached in month %d.' % month}, 'result': result}


def _no_depletion(summary):
    return summary['depletion_month'] is None


def _solve_capital(d, detail):
    if d['withdrawal']['mode'] == 'none':
        raise EngineError([{'field': 'withdrawal.mode', 'message': 'Choose a withdrawal method first.'}])
    high = Decimal(1000)
    ceiling = Decimal(10) ** 12
    while not _no_depletion(_final(_with(d, initial=high))):
        high *= 2
        if high > ceiling:
            return {'no_solution': 'No starting amount up to KES 1 trillion sustains these withdrawals for the whole period.', 'result': _project(_with(d, initial=ceiling), detail)}
    x = _bisect(lambda c: _final(_with(d, initial=c)), Decimal(0), high, _no_depletion, Decimal('0.0001'))
    x = x.quantize(CENT, rounding=ROUND_HALF_UP)
    if not _no_depletion(_final(_with(d, initial=x))):
        x += CENT
    result = _project(_with(d, initial=x), detail)
    return {'solution': {'kind': 'capital_for_withdrawal', 'value': _m(x), 'explanation': 'The smallest starting amount (to the nearest cent) that pays every withdrawal for %s years under these assumptions.' % _plain(d['years'])}, 'result': result}


def _solve_max_withdrawal(d, detail):
    mode = d['withdrawal']['mode']
    if mode not in ('fixed', 'inflation_adjusted'):
        raise EngineError([{'field': 'withdrawal.mode', 'message': 'Choose the fixed or inflation-adjusted withdrawal method to solve for the amount.'}])

    def with_amount(a):
        w = dict(d['withdrawal'])
        w['amount'] = a
        return _with(d, withdrawal=w)

    if not _no_depletion(_final(with_amount(Decimal('0.01')))):
        return {'no_solution': 'Even a very small withdrawal runs out. Check the starting amount and the length of time.', 'result': _project(with_amount(Decimal('0.01')), detail)}
    low, high = Decimal('0.01'), Decimal(1000)
    ceiling = Decimal(10) ** 10
    while _no_depletion(_final(with_amount(high))):
        low = high
        high *= 2
        if high > ceiling:
            return {'no_solution': 'Withdrawals up to KES 10 billion a period are all sustained; the answer is effectively unlimited.', 'result': _project(with_amount(low), detail)}
    # largest amount with no depletion: bisect on the failing side
    for _ in range(120):
        mid = (low + high) / 2
        if _no_depletion(_final(with_amount(mid))):
            low = mid
        else:
            high = mid
        if high - low <= Decimal('0.0001'):
            break
    x = low.quantize(CENT, rounding=ROUND_HALF_UP)
    if not _no_depletion(_final(with_amount(x))):
        x -= CENT
    result = _project(with_amount(x), detail)
    return {'solution': {'kind': 'max_withdrawal', 'value': _m(x), 'explanation': 'The largest %s withdrawal (to the nearest cent) the balance can pay for %s years under these assumptions.' % (d['withdrawal']['frequency'], _plain(d['years']))}, 'result': result}


# ---------------------------------------------------------------- scenarios
def apply_overrides(raw_base, overrides):
    """Merge scenario overrides (dotted keys allowed, e.g. 'withdrawal.amount') into raw base inputs."""
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in raw_base.items()}
    for key, value in (overrides or {}).items():
        if '.' in key:
            head, tail = key.split('.', 1)
            sub = merged.get(head)
            merged[head] = dict(sub) if isinstance(sub, dict) else {}
            merged[head][tail] = value
        else:
            merged[key] = value
    return merged


def compare(raw_base, scenarios, detail=False):
    """Run the base case and up to 5 named scenarios; report what changed and how the results differ."""
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 5:
        raise EngineError([{'field': 'scenarios', 'message': 'Provide 1 to 5 scenarios.'}])
    base_inputs = normalize(raw_base)
    base = project(base_inputs, detail)
    rows = [{'name': 'Base case', 'overrides': {}, 'changes': [], 'result': base, 'is_base': True}]
    for i, item in enumerate(scenarios):
        if not isinstance(item, dict):
            raise EngineError([{'field': f'scenarios[{i}]', 'message': 'Each scenario needs a name and overrides.'}])
        overrides = item.get('overrides') or {}
        merged = apply_overrides(raw_base, overrides)
        try:
            result = project(normalize(merged), detail)
        except EngineError as exc:
            raise EngineError([{'field': f'scenarios[{i}].' + e['field'], 'message': e['message']} for e in exc.errors])
        changes = []
        for key in overrides:
            changes.append({'field': key, 'label': INPUT_LABELS.get(key, key), 'from': _lookup(base['inputs'], key), 'to': _lookup(result['inputs'], key)})
        rows.append({'name': str(item.get('name') or 'Scenario %d' % (i + 1))[:60], 'overrides': overrides, 'changes': changes, 'result': result, 'is_base': False})
    base_final = Decimal(base['summary']['final_balance'])
    for row in rows:
        row['delta_final_balance'] = _m(Decimal(row['result']['summary']['final_balance']) - base_final)
    return {'model': MODEL_ID, 'version': MODEL_VERSION, 'scenarios': rows}


def _lookup(inputs, dotted):
    node = inputs
    for part in dotted.split('.'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node
