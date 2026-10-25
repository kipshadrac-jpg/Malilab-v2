"""Calculators for common Kenyan money products: Treasury bills, Treasury bonds, money market funds, SACCO deposits, loans.

Same promises as the main engine: deterministic, Decimal arithmetic, no Django, every figure traceable.
Every result has ONE shape (the "instrument contract") so the app can show any of them with the same screens:

    model, version, as_of, inputs, headline, metrics[], table, chart, warnings[], assumptions[],
    methodology[], interpretation[], rules[]

Rates and yields are entered by the person (they change daily). Tax rules and day counts come from rules.py, each with
its source and the date it was read, and are shown next to the numbers they affect. Nothing here is a forecast.
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

from . import rules as kenya_rules
from .engine import EngineError, _choice, _dec, _m, normalize, project

MODEL_VERSION = '1.0.0'
MODELS = ('tbill', 'tbond', 'mmf', 'sacco', 'loan')
CENT = Decimal('0.01')
ONE = Decimal(1)
ZERO = Decimal(0)
HUNDRED = Decimal(100)


# ---------------------------------------------------------------- small helpers
def _money(v):
    return Decimal(v).quantize(CENT, rounding=ROUND_HALF_UP)


def kes(v):
    return 'KES ' + format(_money(v), ',.2f')


def pct(v, places=2):
    q = Decimal(1).scaleb(-places)
    return format(Decimal(v).quantize(q, rounding=ROUND_HALF_UP), 'f') + '%'


def _int(value, field, errors, low, high, default=None, required=False):
    n = _dec(value, field, errors, low, high, None if default is None else Decimal(default), required)
    if n is None:
        return default
    if n != n.to_integral_value():
        errors.append({'field': field, 'message': 'Enter a whole number.'})
        return default
    return int(n)


def _flag(value, default=False):
    return default if value is None else bool(value)


def _metric(key, label, value, kind='money'):
    """kind: money (KES), percent, text. `value` is a Decimal for money/percent, text otherwise."""
    if kind == 'money':
        return {'key': key, 'label': label, 'value': kes(value), 'raw': _m(value), 'unit': 'KES'}
    if kind == 'percent':
        return {'key': key, 'label': label, 'value': pct(value), 'raw': format(Decimal(value).quantize(Decimal('0.0001')), 'f'), 'unit': '%'}
    return {'key': key, 'label': label, 'value': str(value), 'raw': str(value), 'unit': ''}


def _assume(label, value, kind, rule_data=None):
    row = {'label': label, 'value': value, 'kind': kind}
    if rule_data:
        row['source'] = kenya_rules.provenance(rule_data)
        row['url'] = rule_data['url']
    return row


def _irr(flows, low=Decimal('-0.9'), high=Decimal(1)):
    """Per-period internal rate of return of equally spaced cash flows (flows[0] is at time 0). None if there is no sign change."""
    def npv(rate):
        v = ONE / (ONE + rate)
        total, f = ZERO, ONE
        for cf in flows:
            total += cf * f
            f *= v
        return total
    a, b = npv(low), npv(high)
    if a == 0:
        return low
    if b == 0:
        return high
    if (a > 0) == (b > 0):
        return None
    for _ in range(200):
        mid = (low + high) / 2
        m = npv(mid)
        if m == 0:
            return mid
        if (m > 0) == (a > 0):
            low, a = mid, m
        else:
            high = mid
        if high - low < Decimal('1e-18'):
            break
    return (low + high) / 2


def _tax_choice(raw, errors, default_rule, as_of, exempt_allowed=True):
    """The tax rate to use: the sourced rule, an override the person typed, or zero for a tax-exempt investor."""
    rule_data = kenya_rules.rule(default_rule, as_of)
    override = _dec(raw.get('tax_rate'), 'tax_rate', errors, 0, 60, None)
    exempt = _flag(raw.get('tax_exempt')) if exempt_allowed else False
    if exempt:
        return ZERO, 'exempt', rule_data
    if override is not None:
        return override, 'user-entered', rule_data
    return Decimal(rule_data['rate']), 'sourced', rule_data


def _as_of(raw, errors):
    value = raw.get('as_of')
    if value in (None, ''):
        return date.today()
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        errors.append({'field': 'as_of', 'message': 'Use a date like 2026-10-19.'})
        return date.today()


def _tax_assumption(label, rate, how, rule_data):
    if how == 'exempt':
        return _assume(label, '0% (you said you are tax exempt)', 'user-entered')
    if how == 'user-entered':
        return _assume(label, pct(rate, 2).replace('.00%', '%') + ' (entered by you; the sourced rate is ' + rule_data['rate'] + '%)', 'user-entered')
    return _assume(label, pct(rate, 2).replace('.00%', '%'), 'sourced', rule_data)


def _finish(model, as_of, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interpretation, rule_list):
    unique, seen = [], set()
    for r in rule_list:
        if r['id'] not in seen:
            seen.add(r['id'])
            unique.append(r)
    return {
        'model': model, 'version': MODEL_VERSION, 'as_of': as_of.isoformat(), 'inputs': inputs, 'headline': headline,
        'metrics': metrics, 'table': table, 'chart': chart, 'warnings': warnings, 'assumptions': assumptions,
        'methodology': methodology, 'interpretation': interpretation, 'rules': unique,
        'conventions': {'currency': 'KES', 'rounding': 'Calculated unrounded; shown to 2 decimal places (half up).'},
    }


def _raise(errors):
    if errors:
        raise EngineError(errors)


def _yrs(v):
    text = format(Decimal(v).normalize(), 'f')
    return text + (' year' if text == '1' else ' years')


def _plain(v):
    if isinstance(v, Decimal):
        text = format(v.normalize(), 'f')
        return text if text != '-0' else '0'
    return v


# ================================================================= Treasury bill
def tbill(raw, as_of=None):
    """One Treasury bill, or the same bill bought again and again with the proceeds (rolling over)."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    when = _as_of(raw, errors)
    amount = _dec(raw.get('amount'), 'amount', errors, 1, 10 ** 11, None, required=True)
    amount_is = _choice(raw.get('amount_is'), 'amount_is', errors, ('face', 'cost'), 'face')
    tenor_raw = raw.get('tenor_days')
    tenor = _int(tenor_raw, 'tenor_days', errors, 1, 400, 91)
    if tenor not in (91, 182, 364):
        errors.append({'field': 'tenor_days', 'message': 'Treasury bills run for 91, 182 or 364 days.'})
    yld = _dec(raw.get('yield_pct'), 'yield_pct', errors, 0, 100, None, required=True)
    basis_rule = kenya_rules.rule('tbill_day_basis', when)
    basis_choice = _choice(str(raw.get('day_basis')) if raw.get('day_basis') not in (None, '') else None, 'day_basis', errors, ('364', '365'), basis_rule['rate'])
    rollovers = _int(raw.get('rollovers'), 'rollovers', errors, 1, 20, 1)
    rate, how, tax_rule = _tax_choice(raw, errors, 'wht_tbill', when)
    _raise(errors)

    with localcontext() as ctx:
        ctx.prec = 50
        basis = Decimal(basis_choice)
        y, d = yld / 100, Decimal(tenor)
        p100 = HUNDRED / (ONE + y * d / basis)
        disc100 = HUNDRED - p100
        tax100 = rate / 100 * disc100
        cost100 = p100 + tax100
        if amount_is == 'face':
            cash0 = amount * cost100 / HUNDRED
        else:
            cash0 = amount
        rows, cash, total_tax, total_disc = [], cash0, ZERO, ZERO
        xs, vals = [0], [cash0]
        for k in range(1, rollovers + 1):
            face = cash * HUNDRED / cost100
            price_amt = face * p100 / HUNDRED
            tax = face * tax100 / HUNDRED
            disc = face * disc100 / HUNDRED
            rows.append([str(k), str(tenor * k), _m(cash), _m(price_amt), _m(tax), _m(face), _m(face - cash)])
            total_tax += tax
            total_disc += disc
            cash = face
            xs.append(k)
            vals.append(face)
        final = cash
        gain = final - cash0
        period_net = cost100 and (HUNDRED / cost100 - ONE)
        days_total = Decimal(tenor * rollovers)
        annual_net = (final / cash0) ** (basis / days_total) - ONE
        simple_net = period_net * basis / d
        first_face = cash0 * HUNDRED / cost100

    tax_label = 'Withholding tax rate'
    metrics = [
        _metric('price_per_100', 'Price per KES 100', p100, 'text') | {'value': format(p100.quantize(Decimal('0.0001')), 'f'), 'raw': format(p100.quantize(Decimal('0.0001')), 'f')},
        _metric('face_value', 'Face value bought first', first_face),
        _metric('first_cost', 'You pay at purchase (price + tax)', cash0),
        _metric('first_tax', 'Tax paid at purchase', first_face * tax100 / HUNDRED),
        _metric('maturity_value', 'You receive at maturity' if rollovers == 1 else 'You hold after the last maturity', final),
        _metric('net_gain', 'Gain after tax', gain),
        _metric('net_period_return', 'Return for one bill, after tax', period_net * 100, 'percent'),
        _metric('net_annual_return', 'Yearly return after tax (compounded)', annual_net * 100, 'percent'),
    ]
    if rollovers > 1:
        metrics.append(_metric('total_tax', 'Tax paid over all purchases', total_tax))
    table = {
        'title': 'Each purchase',
        'columns': [{'key': 'n', 'label': 'Purchase', 'kind': 'text'}, {'key': 'days', 'label': 'Days from start', 'kind': 'text'},
                    {'key': 'cash', 'label': 'Cash used', 'kind': 'money'}, {'key': 'price', 'label': 'Price paid', 'kind': 'money'},
                    {'key': 'tax', 'label': 'Tax at purchase', 'kind': 'money'}, {'key': 'face', 'label': 'Maturity value', 'kind': 'money'},
                    {'key': 'gain', 'label': 'Gain after tax', 'kind': 'money'}],
        'rows': rows,
    }
    chart = {
        'title': 'Cash after each maturity', 'x_label': 'Purchase', 'y_label': 'Cash', 'unit': 'KES', 'x': [str(x) for x in xs],
        'series': [{'key': 'cash', 'name': 'Cash held', 'values': [_m(v) for v in vals]}],
    }
    warnings = []
    if amount_is == 'face' and (amount % 50000 != 0):
        warnings.append({'code': 'denomination', 'message': 'CBK bids are in multiples of KES 50,000 (check the current auction notice for minimums). This amount is not.'})
    if how == 'user-entered' and rate != Decimal(tax_rule['rate']):
        warnings.append({'code': 'tax_override', 'message': 'You changed the tax rate from the sourced %s%%.' % tax_rule['rate']})
    if rollovers > 1:
        warnings.append({'code': 'rollover', 'message': 'Rolling over assumes every new bill is bought at the same yield. Auction yields change every week, so treat this as an illustration.'})
    assumptions = [
        _assume('Amount', kes(amount) + (' face value' if amount_is == 'face' else ' paid at purchase'), 'user-entered'),
        _assume('Bill length', '%d days' % tenor, 'user-entered'),
        _assume('Yield you expect to be accepted', pct(yld) + ' a year', 'assumption'),
        _tax_assumption(tax_label, rate, how, tax_rule),
        _assume('Day count', basis_choice + ' days a year', 'sourced' if basis_choice == basis_rule['rate'] else 'user-entered', basis_rule if basis_choice == basis_rule['rate'] else None),
    ]
    if rollovers > 1:
        assumptions.append(_assume('Rollovers', '%d bills in a row, each bought with the full proceeds of the last' % rollovers, 'user-entered'))
    methodology = [
        'Model tbill version %s.' % MODEL_VERSION,
        'Price per KES 100 = 100 / (1 + yield x days / %s). The discount is 100 minus that price.' % basis_choice,
        'Withholding tax is charged on the discount and paid with the price when you buy. You receive the full face value at maturity.',
        'Return = (face value / what you paid) - 1, shown for one bill and compounded to a year.',
    ]
    s = ('A bill of KES %s face value at a %s yield and %d days costs KES %s per KES 100, %s with tax. '
         % (format(_money(first_face), ',.2f'), pct(yld).replace('.00%', '%'), tenor, format(p100.quantize(Decimal('0.0001')), 'f'),
            kes(cash0)))
    interp = [
        'Under these assumptions, you pay %s at purchase (price plus %s tax) and receive %s at maturity, a gain of %s after tax.'
        % (kes(cash0), kes(first_face * tax100 / HUNDRED), kes(first_face), kes(first_face - cash0)),
        'That is %s for one bill, or about %s a year after tax if the same return could be repeated.' % (pct(period_net * 100), pct(annual_net * 100)),
    ]
    if rollovers > 1:
        interp.append('Buying again %d times with the proceeds would leave %s after %d days, with %s paid in tax along the way.'
                      % (rollovers, kes(final), tenor * rollovers, kes(total_tax)))
    headline = {'label': 'You receive at maturity' if rollovers == 1 else 'You hold at the end', 'value': kes(final),
                'caption': 'Gain after tax: ' + kes(gain)}
    inputs = {'amount': _plain(amount), 'amount_is': amount_is, 'tenor_days': tenor, 'yield_pct': _plain(yld), 'day_basis': basis_choice,
              'rollovers': rollovers, 'tax_rate': _plain(rate) if how == 'user-entered' else None, 'tax_exempt': how == 'exempt', 'as_of': when.isoformat()}
    return _finish('tbill', when, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interp,
                   [tax_rule, basis_rule])


# ================================================================= Treasury bond
def tbond(raw, as_of=None):
    """A fixed-coupon Treasury bond bought at issue (or on a coupon date) and held to maturity."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    when = _as_of(raw, errors)
    face = _dec(raw.get('face'), 'face', errors, 1, 10 ** 11, None, required=True)
    coupon = _dec(raw.get('coupon_rate'), 'coupon_rate', errors, 0, 50, None, required=True)
    tenor = _dec(raw.get('tenor_years'), 'tenor_years', errors, Decimal('0.5'), 40, None, required=True)
    ytm = _dec(raw.get('ytm_pct'), 'ytm_pct', errors, 0, 100, None, required=True)
    infra = _flag(raw.get('infrastructure'))
    n = None
    if tenor is not None:
        if (tenor * 2) != (tenor * 2).to_integral_value():
            errors.append({'field': 'tenor_years', 'message': 'Use whole or half years, such as 5 or 7.5.'})
        else:
            n = int(tenor * 2)
    short_long = 'wht_tbond_long' if (tenor is not None and tenor >= 10) else 'wht_tbond_short'
    if infra:
        short_long = 'infrastructure_bond'
    rate, how, tax_rule = _tax_choice(raw, errors, short_long, when)
    basis_rule = kenya_rules.rule('tbond_day_basis', when)
    _raise(errors)

    with localcontext() as ctx:
        ctx.prec = 50
        half = ytm / 200
        coupon100 = coupon / 2
        if half == 0:
            p100 = coupon100 * n + HUNDRED
        else:
            v = ONE / (ONE + half)
            vk = ONE
            p100 = ZERO
            for k in range(1, n + 1):
                vk *= v
                p100 += coupon100 * vk
            p100 += HUNDRED * vk
        price_amt = face * p100 / HUNDRED
        disc100 = max(ZERO, HUNDRED - p100)
        wht_discount = rate / 100 * disc100 * face / HUNDRED
        cost = price_amt + wht_discount
        coupon_gross = face * coupon / 200
        coupon_tax = coupon_gross * rate / 100
        coupon_net = coupon_gross - coupon_tax
        flows = [-cost] + [coupon_net] * n
        flows[-1] += face
        r = _irr(flows)
        annual_net = ((ONE + r) ** 2 - ONE) if r is not None else None
        total_coupons_net = coupon_net * n
        total_back = total_coupons_net + face
        net_income = total_back - cost
        rows, cum, xs, back, paid = [], ZERO, [], [], []
        xs.append('0'); back.append(ZERO); paid.append(cost)
        for k in range(1, n + 1):
            principal = face if k == n else ZERO
            cash = coupon_net + principal
            cum += cash
            years = Decimal(k) / 2
            rows.append([format(years.normalize(), 'f'), _m(coupon_gross), _m(coupon_tax), _m(coupon_net), _m(principal), _m(cash), _m(cum - cost)])
            xs.append(format(years.normalize(), 'f'))
            back.append(cum)
            paid.append(cost)

    metrics = [
        _metric('price_per_100', 'Price per KES 100', p100, 'text') | {'value': format(p100.quantize(Decimal('0.0001')), 'f'), 'raw': format(p100.quantize(Decimal('0.0001')), 'f')},
        _metric('price_amount', 'Price of the bond', price_amt),
        _metric('tax_on_discount', 'Tax on the discount, paid at purchase', wht_discount),
        _metric('total_cost', 'You pay at purchase', cost),
        _metric('coupon_gross', 'Each coupon, before tax', coupon_gross),
        _metric('coupon_net', 'Each coupon, after tax', coupon_net),
        _metric('total_coupons', 'All coupons, after tax', total_coupons_net),
        _metric('redemption', 'Face value paid back', face),
        _metric('net_income', 'Total gain after tax', net_income),
    ]
    if annual_net is not None:
        metrics.append(_metric('net_annual_return', 'Yearly return after tax (compounded)', annual_net * 100, 'percent'))
    metrics.append(_metric('gross_ytm', 'Yield you entered (before tax)', ytm, 'percent'))
    table = {
        'title': 'Cash received each half year',
        'columns': [{'key': 'year', 'label': 'Year', 'kind': 'text'}, {'key': 'coupon', 'label': 'Coupon', 'kind': 'money'},
                    {'key': 'tax', 'label': 'Tax', 'kind': 'money'}, {'key': 'net', 'label': 'Coupon after tax', 'kind': 'money'},
                    {'key': 'principal', 'label': 'Face value back', 'kind': 'money'}, {'key': 'cash', 'label': 'Cash received', 'kind': 'money'},
                    {'key': 'position', 'label': 'Received minus paid', 'kind': 'money'}],
        'rows': rows,
    }
    chart = {
        'title': 'Cash received compared with what you paid', 'x_label': 'Year', 'y_label': 'Amount', 'unit': 'KES', 'x': xs,
        'series': [{'key': 'back', 'name': 'Cash received so far', 'values': [_m(v) for v in back]},
                   {'key': 'paid', 'name': 'Amount paid', 'values': [_m(v) for v in paid]}],
    }
    warnings = [{'code': 'settlement', 'message': 'This assumes you buy on a coupon date at the yield you entered. Accrued interest, secondary market prices and dealer costs are not included.'}]
    if p100 > HUNDRED:
        warnings.append({'code': 'premium', 'message': 'The yield is below the coupon, so the price is above KES 100. No tax relief on the premium is assumed.'})
    if infra:
        warnings.append({'code': 'infrastructure', 'message': 'Infrastructure bonds are treated as tax free, as in the source. Check the prospectus of the bond and any later Finance Act.'})
    if how == 'user-entered' and rate != Decimal(tax_rule['rate']):
        warnings.append({'code': 'tax_override', 'message': 'You changed the tax rate from the sourced %s%%.' % tax_rule['rate']})
    assumptions = [
        _assume('Face value', kes(face), 'user-entered'),
        _assume('Coupon rate', pct(coupon).replace('.00%', '%') + ' a year, paid every six months', 'user-entered'),
        _assume('Time to maturity', format(tenor.normalize(), 'f') + ' years', 'user-entered'),
        _assume('Yield to maturity you pay', pct(ytm).replace('.00%', '%') + ' a year', 'assumption'),
        _tax_assumption('Withholding tax rate', rate, how, tax_rule),
        _assume('Day count', '364 days a year (half-year periods of 182 days)', 'sourced', basis_rule),
    ]
    methodology = [
        'Model tbond version %s.' % MODEL_VERSION,
        'Price per KES 100 = the present value of every coupon and the KES 100 repaid, discounted at half the yield for each six-month period.',
        'Withholding tax applies to each coupon, and to the discount when the price is below 100. It is paid at purchase for the discount.',
        'Yearly return after tax is the internal rate of return of what you pay and every payment you receive, compounded to a year.',
    ]
    interp = [
        'Under these assumptions, you pay %s (price %s plus %s tax on the discount) and receive %s every six months after tax, then %s back at maturity.'
        % (kes(cost), kes(price_amt), kes(wht_discount), kes(coupon_net), kes(face)),
        'In total you get back %s, a gain of %s after tax%s.' % (kes(total_back), kes(net_income),
            (', about %s a year' % pct(annual_net * 100)) if annual_net is not None else ''),
    ]
    headline = {'label': 'Total gain after tax', 'value': kes(net_income), 'caption': 'Paid %s, receive %s in total' % (kes(cost), kes(total_back))}
    inputs = {'face': _plain(face), 'coupon_rate': _plain(coupon), 'tenor_years': _plain(tenor), 'ytm_pct': _plain(ytm),
              'infrastructure': infra, 'tax_rate': _plain(rate) if how == 'user-entered' else None, 'tax_exempt': how == 'exempt', 'as_of': when.isoformat()}
    return _finish('tbond', when, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interp, [tax_rule, basis_rule])


# ================================================================= money market fund
def mmf(raw, as_of=None):
    """A money market fund: a starting amount and monthly top-ups growing at the fund's yield, with withholding tax."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    when = _as_of(raw, errors)
    basis = _choice(raw.get('yield_basis'), 'yield_basis', errors, ('gross', 'net'), 'gross')
    rate, how, tax_rule = _tax_choice(raw, errors, 'wht_mmf', when)
    quoted = _dec(raw.get('yield_pct'), 'yield_pct', errors, 0, 100, None, required=True)
    engine_raw = {
        'initial': raw.get('initial'), 'years': raw.get('years'), 'annual_return': quoted, 'rate_type': 'effective',
        'contribution': raw.get('contribution'), 'contribution_frequency': 'monthly', 'contribution_timing': 'end',
        'tax_on_growth': rate if basis == 'gross' else 0, 'include_tax': basis == 'gross',
        'include_fees': False, 'include_inflation': bool(raw.get('inflation')), 'inflation': raw.get('inflation'),
        'target': raw.get('target'), 'start_date': raw.get('start_date'),
    }
    try:
        d = normalize(engine_raw)
    except EngineError as exc:
        errors.extend(e for e in exc.errors if e['field'] not in [x['field'] for x in errors])
        raise EngineError(errors)
    _raise(errors)
    r = project(d)
    s = r['summary']
    metrics = [
        _metric('final_balance', 'Value at the end', Decimal(s['final_balance'])),
        _metric('total_contributed', 'Total you put in', Decimal(s['total_contributed'])),
        _metric('total_growth', 'Interest earned', Decimal(s['total_growth'])),
        _metric('total_tax', 'Withholding tax paid', Decimal(s['total_tax'])),
        _metric('net_growth', 'Interest after tax', Decimal(s['net_growth'])),
    ]
    if d['include_inflation'] and d['inflation']:
        metrics.append(_metric('final_real_balance', "Value in today's money", Decimal(s['final_real_balance'])))
    rows = [[a['year'], a['opening'], a['contributions'], a['growth'], a['tax'], a['closing']] for a in r['annual']]
    table = {
        'title': 'Year by year',
        'columns': [{'key': 'year', 'label': 'Year', 'kind': 'text'}, {'key': 'opening', 'label': 'Opening', 'kind': 'money'},
                    {'key': 'contributions', 'label': 'Put in', 'kind': 'money'}, {'key': 'growth', 'label': 'Interest', 'kind': 'money'},
                    {'key': 'tax', 'label': 'Tax', 'kind': 'money'}, {'key': 'closing', 'label': 'Closing', 'kind': 'money'}],
        'rows': rows,
    }
    chart = {
        'title': 'How the fund grows', 'x_label': 'Year', 'y_label': 'Value', 'unit': 'KES',
        'x': [('%d' % (p['month'] // 12)) if p['month'] % 12 == 0 else ('%.1f' % (p['month'] / 12)) for p in r['series']],
        'series': [{'key': 'closing', 'name': 'Fund value', 'values': [p['closing'] for p in r['series']]},
                   {'key': 'total_contributed', 'name': 'Money put in', 'values': [p['total_contributed'] for p in r['series']]}],
    }
    warnings = [{'code': 'variable', 'message': 'Money market fund yields change daily and are not guaranteed. This uses one yield for the whole period.'}]
    if basis == 'gross':
        warnings.append({'code': 'gross', 'message': 'You entered a yield before withholding tax. If the fund already quotes its yield after tax, choose "net" instead so tax is not taken twice.'})
    warnings.extend(r['warnings'])
    assumptions = [
        _assume('Starting amount', kes(d['initial']), 'user-entered'),
        _assume('Monthly top-up', kes(d['contribution']), 'user-entered'),
        _assume('Duration', _yrs(d['years']), 'user-entered'),
        _assume('Yield', pct(quoted).replace('.00%', '%') + ' a year, effective, ' + ('before withholding tax' if basis == 'gross' else 'already after tax'), 'assumption'),
    ]
    if basis == 'gross':
        assumptions.append(_tax_assumption('Withholding tax rate', rate, how, tax_rule))
    methodology = ['Model mmf version %s, using the compound-projection engine.' % MODEL_VERSION] + r['methodology'][1:] + [
        'The yearly yield is converted to an equivalent monthly rate. Tax is taken from each month\'s interest, as funds deduct it before crediting you.']
    interp = [
        'Under these assumptions, the fund would be worth %s after %s, from %s put in and %s of interest after tax.'
        % (kes(Decimal(s['final_balance'])), _yrs(d['years']), kes(Decimal(s['total_contributed'])), kes(Decimal(s['net_growth']))),
    ]
    if Decimal(s['total_tax']) > 0:
        interp.append('Withholding tax at %s%% would take %s of the interest.' % (format(rate.normalize(), 'f'), kes(Decimal(s['total_tax']))))
    headline = {'label': 'Value at the end', 'value': kes(Decimal(s['final_balance'])), 'caption': 'Interest after tax: ' + kes(Decimal(s['net_growth']))}
    inputs = {'initial': _plain(d['initial']), 'contribution': _plain(d['contribution']), 'years': _plain(d['years']), 'yield_pct': _plain(quoted),
              'yield_basis': basis, 'tax_rate': _plain(rate) if how == 'user-entered' else None, 'tax_exempt': how == 'exempt', 'inflation': _plain(d['inflation']) if d['include_inflation'] else None,
              'as_of': when.isoformat()}
    return _finish('mmf', when, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interp, [tax_rule] if basis == 'gross' else [])


# ================================================================= SACCO deposits
def sacco(raw, as_of=None):
    """SACCO deposits earning a yearly dividend on the average balance, reinvested or paid out."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    when = _as_of(raw, errors)
    initial = _dec(raw.get('initial'), 'initial', errors, 0, 10 ** 11, ZERO)
    contribution = _dec(raw.get('contribution'), 'contribution', errors, 0, 10 ** 10, ZERO)
    years = _int(raw.get('years'), 'years', errors, 1, 60, None, required=True)
    rate_in = _dec(raw.get('dividend_pct'), 'dividend_pct', errors, 0, 100, None, required=True)
    payout = _choice(raw.get('payout'), 'payout', errors, ('reinvest', 'cash'), 'reinvest')
    rate, how, tax_rule = _tax_choice(raw, errors, 'wht_dividend_resident', when)
    _raise(errors)

    with localcontext() as ctx:
        ctx.prec = 50
        bal = initial
        put_in = initial
        paid_out = ZERO
        total_div = ZERO
        total_tax = ZERO
        rows, xs, bals, ins, outs = [], ['0'], [initial], [initial], [ZERO]
        for yr in range(1, years + 1):
            opening = bal
            month_ends = []
            for _m_ in range(12):
                bal += contribution
                put_in += contribution
                month_ends.append(bal)
            avg = sum(month_ends) / 12
            div = avg * rate_in / 100
            tax = div * rate / 100
            net = div - tax
            total_div += div
            total_tax += tax
            if payout == 'reinvest':
                bal += net
            else:
                paid_out += net
            rows.append([str(yr), _m(opening), _m(contribution * 12), _m(avg), _m(div), _m(tax), _m(net), _m(bal)])
            xs.append(str(yr)); bals.append(bal); ins.append(put_in); outs.append(paid_out)
        net_div = total_div - total_tax
        total_value = bal + paid_out

    metrics = [
        _metric('deposits_end', 'Deposits at the end', bal),
        _metric('total_contributed', 'Total you put in', put_in),
        _metric('total_dividends', 'Dividends before tax', total_div),
        _metric('total_tax', 'Tax on dividends', total_tax),
        _metric('net_dividends', 'Dividends after tax', net_div),
    ]
    if payout == 'cash':
        metrics.append(_metric('paid_out', 'Dividends received in cash', paid_out))
    metrics.append(_metric('total_value', 'Deposits plus dividends received', total_value))
    table = {
        'title': 'Year by year',
        'columns': [{'key': 'year', 'label': 'Year', 'kind': 'text'}, {'key': 'opening', 'label': 'Opening', 'kind': 'money'},
                    {'key': 'contributed', 'label': 'Put in', 'kind': 'money'}, {'key': 'average', 'label': 'Average balance', 'kind': 'money'},
                    {'key': 'dividend', 'label': 'Dividend', 'kind': 'money'}, {'key': 'tax', 'label': 'Tax', 'kind': 'money'},
                    {'key': 'net', 'label': 'Dividend after tax', 'kind': 'money'}, {'key': 'closing', 'label': 'Deposits at year end', 'kind': 'money'}],
        'rows': rows,
    }
    series = [{'key': 'deposits', 'name': 'Deposits', 'values': [_m(v) for v in bals]},
              {'key': 'put_in', 'name': 'Money put in', 'values': [_m(v) for v in ins]}]
    if payout == 'cash':
        series.append({'key': 'cash', 'name': 'Dividends received', 'values': [_m(v) for v in outs]})
    chart = {'title': 'Deposits over time', 'x_label': 'Year', 'y_label': 'Amount', 'unit': 'KES', 'x': xs, 'series': series}
    warnings = [
        {'code': 'dividend_not_promised', 'message': 'A SACCO sets its dividend each year at its annual general meeting. It is not guaranteed and can be lower or zero.'},
        {'code': 'approximation', 'message': 'This pays the dividend on the average of your month-end balances. Your SACCO may use another basis, such as opening balance or shares only.'},
    ]
    if how == 'user-entered' and rate != Decimal(tax_rule['rate']):
        warnings.append({'code': 'tax_override', 'message': 'You changed the tax rate from %s%%.' % tax_rule['rate']})
    assumptions = [
        _assume('Starting deposits', kes(initial), 'user-entered'),
        _assume('Monthly deposit', kes(contribution), 'user-entered'),
        _assume('Duration', _yrs(years), 'user-entered'),
        _assume('Dividend rate', pct(rate_in).replace('.00%', '%') + ' a year on the average balance', 'assumption'),
        _assume('Dividends', 'added to your deposits each year' if payout == 'reinvest' else 'paid out to you in cash each year', 'user-entered'),
        _tax_assumption('Tax on dividends', rate, how, tax_rule),
    ]
    methodology = [
        'Model sacco version %s.' % MODEL_VERSION,
        'Each month you add your deposit. At the end of each year the dividend is the dividend rate times the average of that year\'s 12 month-end balances.',
        'Withholding tax is taken from the dividend. The rest is added to your deposits or paid out, as you chose.',
    ]
    interp = [
        'Under these assumptions, you would put in %s over %s and earn %s in dividends after tax (%s before tax).'
        % (kes(put_in), _yrs(years), kes(net_div), kes(total_div)),
        ('Your deposits would stand at %s.' % kes(bal)) if payout == 'reinvest' else
        ('Your deposits would stand at %s, and you would have received %s in cash dividends.' % (kes(bal), kes(paid_out))),
    ]
    headline = {'label': 'Deposits plus dividends', 'value': kes(total_value), 'caption': 'Dividends after tax: ' + kes(net_div)}
    inputs = {'initial': _plain(initial), 'contribution': _plain(contribution), 'years': years, 'dividend_pct': _plain(rate_in), 'payout': payout,
              'tax_rate': _plain(rate) if how == 'user-entered' else None, 'tax_exempt': how == 'exempt', 'as_of': when.isoformat()}
    return _finish('sacco', when, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interp, [tax_rule])


# ================================================================= loans
def loan(raw, as_of=None):
    """A loan repaid in equal monthly instalments, on a reducing balance or a flat rate, with the real cost including fees."""
    if not isinstance(raw, dict):
        raise EngineError([{'field': 'inputs', 'message': 'Inputs must be an object.'}])
    errors = []
    when = _as_of(raw, errors)
    principal = _dec(raw.get('principal'), 'principal', errors, 1, 10 ** 11, None, required=True)
    rate = _dec(raw.get('rate_pct'), 'rate_pct', errors, 0, 300, None, required=True)
    months = _int(raw.get('term_months'), 'term_months', errors, 1, 600, None, required=True)
    method = _choice(raw.get('method'), 'method', errors, ('reducing', 'flat'), 'reducing')
    fee_pct = _dec(raw.get('processing_fee_pct'), 'processing_fee_pct', errors, 0, 30, ZERO)
    ins_pct = _dec(raw.get('insurance_pct'), 'insurance_pct', errors, 0, 30, ZERO)
    _raise(errors)

    with localcontext() as ctx:
        ctx.prec = 50
        n = Decimal(months)
        r = rate / 1200
        if method == 'flat':
            interest_total = principal * rate / 100 * n / 12
            payment = (principal + interest_total) / n
        elif r == 0:
            payment = principal / n
            interest_total = ZERO
        else:
            payment = principal * r / (ONE - (ONE + r) ** (-months))
            interest_total = payment * n - principal
        fees = principal * (fee_pct + ins_pct) / 100
        received = principal - fees
        total_repaid = payment * n
        total_cost = interest_total + fees
        irr_all = _irr([received] + [-payment] * months, Decimal('-0.5'), Decimal(5))
        irr_plain = _irr([principal] + [-payment] * months, Decimal('-0.5'), Decimal(5))
        eff_all = ((ONE + irr_all) ** 12 - ONE) if irr_all is not None else None
        nominal_all = irr_all * 12 if irr_all is not None else None
        nominal_plain = irr_plain * 12 if irr_plain is not None else None
        rows, bal, cum_int = [], principal, ZERO
        step = max(1, -(-months // 24))
        xs, bals, ints = ['0'], [principal], [ZERO]
        for k in range(1, months + 1):
            interest = (interest_total / n) if method == 'flat' else bal * r
            princ = (principal / n) if method == 'flat' else payment - interest
            bal -= princ
            if k == months:
                bal = ZERO if abs(bal) < Decimal('0.0001') else bal
            cum_int += interest
            rows.append([str(k), _m(bal + princ), _m(interest), _m(princ), _m(payment), _m(bal)])
            if k % step == 0 or k == months:
                xs.append(str(k)); bals.append(bal); ints.append(cum_int)

    metrics = [
        _metric('payment', 'Monthly payment', payment),
        _metric('total_repaid', 'Total you repay', total_repaid),
        _metric('total_interest', 'Total interest', interest_total),
    ]
    if fees > 0:
        metrics.append(_metric('fees', 'Fees paid up front', fees))
        metrics.append(_metric('received', 'You actually receive', received))
    metrics.append(_metric('total_cost', 'Total cost of the loan', total_cost))
    if eff_all is not None:
        metrics.append(_metric('effective_rate', 'True yearly cost (compounded)', eff_all * 100, 'percent'))
        metrics.append(_metric('nominal_apr', 'True cost as a yearly rate', nominal_all * 100, 'percent'))
    if method == 'flat' and nominal_plain is not None:
        metrics.append(_metric('equivalent_reducing', 'Same cost as a reducing-balance rate of', nominal_plain * 100, 'percent'))
    table = {
        'title': 'Repayment schedule',
        'columns': [{'key': 'month', 'label': 'Month', 'kind': 'text'}, {'key': 'opening', 'label': 'Owed at start', 'kind': 'money'},
                    {'key': 'interest', 'label': 'Interest', 'kind': 'money'}, {'key': 'principal', 'label': 'Principal', 'kind': 'money'},
                    {'key': 'payment', 'label': 'Payment', 'kind': 'money'}, {'key': 'closing', 'label': 'Owed at end', 'kind': 'money'}],
        'rows': rows,
    }
    chart = {
        'title': 'What you owe and what you have paid in interest', 'x_label': 'Month', 'y_label': 'Amount', 'unit': 'KES', 'x': xs,
        'series': [{'key': 'balance', 'name': 'Still owed', 'values': [_m(v) for v in bals]},
                   {'key': 'interest', 'name': 'Interest paid so far', 'values': [_m(v) for v in ints]}],
    }
    warnings = []
    if method == 'flat':
        warnings.append({'code': 'flat', 'message': 'A flat rate charges interest on the full amount for the whole term, even as you repay it. That makes it cost more than the same rate on a reducing balance.'})
    if fees > 0:
        warnings.append({'code': 'fees', 'message': 'Fees paid up front reduce the money you actually get while you still repay the full amount, so the true cost is higher than the quoted rate.'})
    assumptions = [
        _assume('Loan amount', kes(principal), 'user-entered'),
        _assume('Quoted interest rate', pct(rate).replace('.00%', '%') + ' a year, ' + ('on a reducing balance' if method == 'reducing' else 'flat (on the full amount for the whole term)'), 'user-entered'),
        _assume('Term', '%d months' % months, 'user-entered'),
    ]
    if fees > 0:
        assumptions.append(_assume('Up-front fees', '%s%% processing + %s%% insurance = %s' % (format(fee_pct.normalize(), 'f'), format(ins_pct.normalize(), 'f'), kes(fees)), 'user-entered'))
    methodology = [
        'Model loan version %s.' % MODEL_VERSION,
        ('Monthly payment = loan x r / (1 - (1 + r)^-months), with r the quoted yearly rate divided by 12.' if method == 'reducing'
         else 'Flat interest = loan x rate x years. The monthly payment is (loan + that interest) / months.'),
        'The true cost is the yearly rate that makes the money you receive equal to the present value of every payment (the internal rate of return).',
    ]
    interp = [
        'Under these assumptions, you would repay %s a month for %d months, %s in total, of which %s is interest.' % (kes(payment), months, kes(total_repaid), kes(interest_total)),
    ]
    if eff_all is not None:
        interp.append('Counting fees, the loan really costs about %s a year (compounded), compared with the %s quoted.' % (pct(eff_all * 100), pct(rate).replace('.00%', '%')))
    if method == 'flat' and nominal_plain is not None:
        interp.append('A flat rate of %s over this term costs the same as about %s on a reducing balance.' % (pct(rate).replace('.00%', '%'), pct(nominal_plain * 100)))
    headline = {'label': 'Monthly payment', 'value': kes(payment), 'caption': 'Total cost of the loan: ' + kes(total_cost)}
    inputs = {'principal': _plain(principal), 'rate_pct': _plain(rate), 'term_months': months, 'method': method,
              'processing_fee_pct': _plain(fee_pct), 'insurance_pct': _plain(ins_pct), 'as_of': when.isoformat()}
    return _finish('loan', when, inputs, headline, metrics, table, chart, warnings, assumptions, methodology, interp, [])


RUNNERS = {'tbill': tbill, 'tbond': tbond, 'mmf': mmf, 'sacco': sacco, 'loan': loan}
ANALYSES = ('sensitivity', 'stress', 'compare')


def run(model, raw):
    if model in ANALYSES:
        from . import analysis  # imported here because analysis builds on this module
        return getattr(analysis, model)(raw if isinstance(raw, dict) else {})
    if model not in RUNNERS:
        raise EngineError([{'field': 'model', 'message': 'Unknown model. Choose one of: ' + ', '.join(MODELS + ANALYSES) + '.'}])
    return RUNNERS[model](raw)
