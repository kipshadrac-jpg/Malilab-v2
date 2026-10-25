"""A small Safaricom Daraja client for M-Pesa Express (STK push). Standard library only.

Settings (from the environment file): MPESA_ENV (sandbox or production), MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET,
MPESA_SHORTCODE, MPESA_PASSKEY, MPESA_CALLBACK_SECRET, MPESA_CALLBACK_BASE, MPESA_TRANSACTION_TYPE.
"""
import base64
import json
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache

SANDBOX = 'https://sandbox.safaricom.co.ke'
LIVE = 'https://api.safaricom.co.ke'
TOKEN_KEY = 'daraja-token'


class DarajaError(Exception):
    pass


def _cfg(name, default=''):
    return getattr(settings, name, default) or default


def sandbox():
    return _cfg('MPESA_ENV', 'sandbox').strip().lower() != 'production'


def base_url():
    return SANDBOX if sandbox() else LIVE


def missing():
    """Names of the settings that are still empty."""
    need = ['MPESA_CONSUMER_KEY', 'MPESA_CONSUMER_SECRET', 'MPESA_SHORTCODE', 'MPESA_PASSKEY', 'MPESA_CALLBACK_SECRET', 'MPESA_CALLBACK_BASE']
    return [n for n in need if not _cfg(n)]


def callback_url():
    return '%s/api/v1/billing/mpesa/callback/%s/' % (_cfg('MPESA_CALLBACK_BASE').rstrip('/'), _cfg('MPESA_CALLBACK_SECRET'))


def _request(method, url, headers, body=None):
    """The one place that touches the network (tests replace it). Returns (http status, parsed JSON or {})."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            status, text = resp.status, resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        status, text = exc.code, exc.read().decode('utf-8', 'replace')
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DarajaError('Could not reach M-Pesa: %s' % exc)
    try:
        return status, json.loads(text) if text else {}
    except ValueError:
        return status, {}


def access_token():
    token = cache.get(TOKEN_KEY)
    if token:
        return token
    if missing():
        raise DarajaError('M-Pesa is not set up yet (missing: %s).' % ', '.join(missing()))
    raw = base64.b64encode(('%s:%s' % (_cfg('MPESA_CONSUMER_KEY'), _cfg('MPESA_CONSUMER_SECRET'))).encode()).decode()
    status, data = _request('GET', base_url() + '/oauth/v1/generate?grant_type=client_credentials', {'Authorization': 'Basic ' + raw})
    token = data.get('access_token')
    if status != 200 or not token:
        raise DarajaError('M-Pesa sign-in failed (HTTP %s). Check the consumer key and secret.' % status)
    cache.set(TOKEN_KEY, token, 50 * 60)
    return token


def _stamp():
    ts = datetime.now(ZoneInfo('Africa/Nairobi')).strftime('%Y%m%d%H%M%S')
    pw = base64.b64encode(('%s%s%s' % (_cfg('MPESA_SHORTCODE'), _cfg('MPESA_PASSKEY'), ts)).encode()).decode()
    return ts, pw


def _call(path, body):
    headers = {'Authorization': 'Bearer ' + access_token(), 'Content-Type': 'application/json'}
    status, data = _request('POST', base_url() + path, headers, body)
    if status == 401:           # token went stale early
        cache.delete(TOKEN_KEY)
        headers['Authorization'] = 'Bearer ' + access_token()
        status, data = _request('POST', base_url() + path, headers, body)
    return status, data


def stk_push(payment):
    """Ask Safaricom to put the payment prompt on the customer's phone."""
    ts, pw = _stamp()
    body = {
        'BusinessShortCode': _cfg('MPESA_SHORTCODE'), 'Password': pw, 'Timestamp': ts,
        'TransactionType': _cfg('MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline'),
        'Amount': int(payment.amount), 'PartyA': payment.phone, 'PartyB': _cfg('MPESA_SHORTCODE'), 'PhoneNumber': payment.phone,
        'CallBackURL': callback_url(), 'AccountReference': ('ML%s' % payment.pk)[:12],
        'TransactionDesc': ('MaliLab %s' % ('all' if payment.product == 'all' else 'module'))[:20],
    }
    status, data = _call('/mpesa/stkpush/v1/processrequest', body)
    if status != 200 or str(data.get('ResponseCode', '')) != '0':
        raise DarajaError(data.get('errorMessage') or data.get('ResponseDescription') or 'M-Pesa did not accept the request (HTTP %s).' % status)
    return data


def stk_query(checkout_request_id):
    """Ask Safaricom how a prompt ended. Returns {'ResultCode': str, 'ResultDesc': str}, or {} while it is still in progress."""
    ts, pw = _stamp()
    status, data = _call('/mpesa/stkpushquery/v1/query', {
        'BusinessShortCode': _cfg('MPESA_SHORTCODE'), 'Password': pw, 'Timestamp': ts, 'CheckoutRequestID': checkout_request_id,
    })
    if status != 200 or 'ResultCode' not in data:
        return {}               # "still being processed" comes back as an HTTP error
    return {'ResultCode': str(data.get('ResultCode')), 'ResultDesc': str(data.get('ResultDesc', ''))}
