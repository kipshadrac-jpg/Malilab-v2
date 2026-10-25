"""What is for sale. Prices are whole Kenya shillings.

A module is bought on its own and is the learner's for good. The all-modules pass is also for good.
Nothing here renews or charges again by itself.
"""
from django.conf import settings

TRIAL_DAYS = 3
MODULE_PRICE = 100
ALL_PRICE = 900


def paywall_on():
    """When off (the default), every module is open to everyone and nothing is checked. Switch on with MALILAB_PAYWALL=1."""
    return bool(getattr(settings, 'MALILAB_PAYWALL', False))


def all_covers_future():
    """True: the all-modules pass also opens modules published later. False: only modules that existed on the day it was bought."""
    return bool(getattr(settings, 'MALILAB_ALL_COVERS_FUTURE', True))


def providers():
    return [p for p in getattr(settings, 'MALILAB_PAY_PROVIDERS', ['mpesa']) if p]


def price_of(product):
    return ALL_PRICE if product == 'all' else MODULE_PRICE
