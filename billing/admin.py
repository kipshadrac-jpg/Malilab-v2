"""Staff screens for payments and what learners own (OTP admin site). Payments are records: they cannot be added or deleted here."""
import csv

from django.contrib import admin
from django.http import HttpResponse

from config.admin_site import admin_site
from .models import Entitlement, ModuleUnlock, Payment
from .reports import sales_summary


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'product', 'module', 'amount', 'status', 'receipt', 'phone', 'sandbox')
    list_filter = ('status', 'product', 'sandbox')
    search_fields = ('user__email', 'receipt', 'phone', 'checkout_request_id')
    date_hierarchy = 'created_at'
    readonly_fields = [f.name for f in Payment._meta.fields]
    actions = ['export_csv']

    def changelist_view(self, request, extra_context=None):
        extra = dict(extra_context or {})
        extra['sales'] = sales_summary()
        return super().changelist_view(request, extra_context=extra)

    @admin.action(description='Download the selected payments as a CSV file')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="malilab-payments.csv"'
        out = csv.writer(response)
        out.writerow(['created', 'paid', 'email', 'product', 'module', 'amount_kes', 'status', 'mpesa_receipt', 'phone', 'test_mode'])
        for p in queryset.select_related('user', 'module'):
            out.writerow([p.created_at.isoformat(), p.paid_at.isoformat() if p.paid_at else '', p.user.email, p.product,
                          p.module.slug if p.module_id else '', p.amount, p.status, p.receipt, p.phone, 'yes' if p.sandbox else 'no'])
        return response

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user', 'trial_started_at', 'all_modules_at', 'note')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)


class ModuleUnlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'source', 'created_at')
    search_fields = ('user__email', 'module__slug')
    raw_id_fields = ('user', 'module', 'payment')


admin_site.register(Payment, PaymentAdmin)
admin_site.register(Entitlement, EntitlementAdmin)
admin_site.register(ModuleUnlock, ModuleUnlockAdmin)
