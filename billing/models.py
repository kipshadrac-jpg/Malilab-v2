from django.conf import settings
from django.db import models


class Entitlement(models.Model):
    """One row per learner: when the free trial began, and whether they hold the all-modules pass."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entitlement')
    trial_started_at = models.DateTimeField()
    all_modules_at = models.DateTimeField(null=True, blank=True, help_text='Set when the all-modules pass was bought or granted. Clear it to take the pass away.')
    note = models.CharField(max_length=300, blank=True, help_text='Why this was changed by hand, if it was.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Entitlement for %s' % self.user_id


class Payment(models.Model):
    """One attempt to pay. Kept for good as the record of the money."""
    PRODUCTS = [('module', 'One module'), ('all', 'All modules')]
    STATUSES = [('pending', 'Waiting for the phone'), ('paid', 'Paid'), ('failed', 'Failed'), ('cancelled', 'Cancelled'),
                ('expired', 'Expired'), ('review', 'Needs a look')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='payments')
    provider = models.CharField(max_length=16, default='mpesa')
    product = models.CharField(max_length=8, choices=PRODUCTS)
    module = models.ForeignKey('content.Module', null=True, blank=True, on_delete=models.PROTECT, related_name='payments')
    amount = models.PositiveIntegerField()
    phone = models.CharField(max_length=15, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default='pending', db_index=True)
    merchant_request_id = models.CharField(max_length=64, blank=True)
    checkout_request_id = models.CharField(max_length=64, blank=True, db_index=True)
    customer_message = models.CharField(max_length=300, blank=True)
    result_code = models.CharField(max_length=16, blank=True)
    result_desc = models.CharField(max_length=300, blank=True)
    receipt = models.CharField(max_length=40, blank=True, db_index=True)
    callback = models.JSONField(null=True, blank=True)
    sandbox = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['user', 'status'], name='payment_user_status_idx')]

    def __str__(self):
        return '%s KES %s (%s)' % (self.product, self.amount, self.status)


class ModuleUnlock(models.Model):
    """A module that is this learner's for good."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='module_unlocks')
    module = models.ForeignKey('content.Module', on_delete=models.PROTECT, related_name='unlocks')
    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name='unlocks')
    source = models.CharField(max_length=16, default='payment', choices=[('payment', 'Payment'), ('grant', 'Given by staff')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'module'], name='unlock_user_module_uniq')]
