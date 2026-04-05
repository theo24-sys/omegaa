from django.contrib import admin
from .models import PaymentPlan, Payment

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'duration_days', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'payment_method', 'status', 'created_at', 'payment_date')
    list_filter = ('status', 'payment_method', 'plan__plan_type')
    search_fields = ('user__username', 'transaction_id', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('user', 'plan', 'amount', 'payment_method')}),
        ('Transaction Details', {'fields': ('transaction_id', 'phone_number', 'payment_date')}),
        ('Status & Notes', {'fields': ('status', 'verification_notes', 'admin_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )