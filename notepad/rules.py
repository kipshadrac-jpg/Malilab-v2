"""Kenyan rules the instrument calculators rely on, each with where it came from and when it applies.

Nothing here is invented. Every rule says which source it was read from, on which date, and what is uncertain.
A rule can have several versions with start dates; the calculator uses the version in force on the date asked for.
Rates are percentages as strings. Changing a rule means adding a version here, with its source, never editing history.
"""
from datetime import date

RETRIEVED = '2026-10-19'

CBK_FAQ = 'https://www.centralbank.go.ke/images/FAQs/FAQsGoKSecurities.pdf'
KRA_WHT = 'https://www.kra.go.ke/images/publications/Withholding-Income-Tax_8112023.pdf'
KRA_DIVIDENDS = 'https://www.kra.go.ke/news-center/blog/1016-taxation-of-dividends'
SERRARI_MMF = 'https://serrarigroup.com/guides/wealth-builder/mmf-tax-kenya-how-much-withholding-tax-do-you-pay'
SERRARI_TBILLS = 'https://serrarigroup.com/serrari-treasury-bills/'
EASTLEIGH_INFRA = 'https://eastleighvoice.co.ke/national/94971/national-assembly-rejects-5-per-cent-tax-on-infrastructure-bonds-interest'
BUSINESS_DAILY_INFRA = 'https://www.businessdailyafrica.com/bd/markets/capital-markets/infrastructure-bonds-face-5pc-tax-4623134'

# Each rule: id -> list of versions (oldest first). 'effective_from' None means the source does not state a start date.
RULES = {
    'wht_tbill': [{
        'label': 'Withholding tax on the discount of a Treasury bill',
        'rate': '15', 'effective_from': None, 'status': 'As stated by the source; start date not given.',
        'source': 'Central Bank of Kenya, FAQs on Government securities', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'Paid when you buy, on top of the price. An investor with a KRA tax exemption certificate does not pay it.',
    }],
    'wht_tbond_short': [{
        'label': 'Withholding tax on Treasury bond interest and discount (tenor up to 9 years)',
        'rate': '15', 'effective_from': None, 'status': 'As stated by the source; start date not given.',
        'source': 'Central Bank of Kenya, FAQs on Government securities', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'Charged on each coupon and on the discount, which is worked out on the clean price. Exempt investors present a KRA certificate.',
    }],
    'wht_tbond_long': [{
        'label': 'Withholding tax on Treasury bond interest and discount (tenor 10 years or more)',
        'rate': '10', 'effective_from': None, 'status': 'As stated by the source; start date not given.',
        'source': 'Central Bank of Kenya, FAQs on Government securities', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'The same document and the KRA withholding tax guide both list 10% for bearer bonds of ten years or more.',
    }],
    'infrastructure_bond': [{
        'label': 'Tax on infrastructure bond interest and discount',
        'rate': '0', 'effective_from': None, 'status': 'Exempt per the source. A 5% tax proposed in 2024 was rejected by the National Assembly on 4 December 2024.',
        'source': 'Central Bank of Kenya, FAQs on Government securities; Eastleigh Voice, 5 Dec 2024', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'Check the prospectus of the specific bond and any later Finance Act. The proposal is reported at ' + EASTLEIGH_INFRA + ' (earlier proposal: ' + BUSINESS_DAILY_INFRA + ').',
    }],
    'wht_mmf': [{
        'label': 'Withholding tax on money market fund interest',
        'rate': '15', 'effective_from': None, 'status': 'Described as the general rate on interest; no statute section was found.',
        'source': 'Serrari Group guide (secondary source); KRA lists 15% on bank interest', 'url': SERRARI_MMF, 'retrieved': RETRIEVED,
        'caveat': 'Funds deduct it before crediting you. Advertised yields are often before tax, so check whether a fund quotes gross or net.',
    }],
    'wht_bank_interest': [{
        'label': 'Withholding tax on bank savings interest paid to residents',
        'rate': '15', 'effective_from': None, 'status': 'KRA lists 15% on interest paid to residents; start date not given in the guide.',
        'source': 'Kenya Revenue Authority, Withholding Income Tax guide', 'url': KRA_WHT, 'retrieved': RETRIEVED,
        'caveat': 'Banks deduct it before crediting you. Check your bank statement for the rate actually applied.',
    }],
    'wht_dividend_resident': [{
        'label': 'Withholding tax on dividends paid to residents',
        'rate': '5', 'effective_from': None, 'status': 'KRA page dated 30 Nov 2020; the KRA 2023/24 guide also lists 5% for resident qualifying dividends.',
        'source': 'Kenya Revenue Authority, Taxation of dividends; KRA Withholding Income Tax guide 2023/24', 'url': KRA_DIVIDENDS, 'retrieved': RETRIEVED,
        'caveat': 'The sources found do not say how SACCO dividends are treated. This rate is used as an assumption; confirm with your SACCO.',
    }],
    'tbill_day_basis': [{
        'label': 'Day count used to price Treasury bills',
        'rate': '365', 'effective_from': None, 'status': 'Price = Face / (1 + yield x days / 365), as given by CBK and a second source.',
        'source': 'Central Bank of Kenya, FAQs on Government securities; Serrari Group Treasury bills guide', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'The CBK document text is partly garbled, so the 365 was confirmed against a second source. Treasury bonds use 364.',
    }],
    'tbond_day_basis': [{
        'label': 'Day count used to price Treasury bonds',
        'rate': '364', 'effective_from': None, 'status': 'Stated by CBK: "The Day Count Convention for pricing Treasury bonds in Kenya is 364 days."',
        'source': 'Central Bank of Kenya, FAQs on Government securities', 'url': CBK_FAQ, 'retrieved': RETRIEVED,
        'caveat': 'With a 364-day year, a half-year coupon period is exactly 182 days, so the half-yearly yield is half the annual yield.',
    }],
}


_loader = None


def set_loader(fn):
    """The website registers a function that returns the rule versions kept in the database. Without one, the values above are used."""
    global _loader
    _loader = fn


def _versions(rule_id):
    if rule_id not in RULES:
        raise KeyError(rule_id)
    if _loader is not None:
        try:
            rows = _loader(rule_id)
        except Exception:  # the database may be unavailable or not migrated yet; the built-in values are always safe
            rows = None
        if rows:
            return rows
    return RULES[rule_id]


def rule(rule_id, as_of=None):
    """The version of a rule in force on [as_of] (a date; today when omitted). Raises KeyError for an unknown rule."""
    versions = _versions(rule_id)
    when = as_of or date.today()
    chosen = None
    for v in versions:
        start = v['effective_from']
        if start is None or start <= when:
            chosen = v
    if chosen is None:
        chosen = versions[0]
    out = {k: v for k, v in chosen.items() if k != 'effective_from'}
    out['id'] = rule_id
    out['effective_from'] = chosen['effective_from'].isoformat() if chosen['effective_from'] else None
    out.setdefault('stamp', 'builtin')
    return out


def provenance(rule_data):
    """Short text for an assumption row: where the value came from."""
    start = rule_data['effective_from'] or 'start date not stated by the source'
    return '%s (%s); read on %s' % (rule_data['source'], start, rule_data['retrieved'])


def all_rules(as_of=None):
    """Every rule as in force on [as_of], for the app's "Rules used" screen."""
    return [rule(k, as_of) for k in RULES]
