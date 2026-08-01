from django.contrib import admin
from .models import PaymentPlan, Payment, MonthlyContribution

@admin.register(MonthlyContribution)
class MonthlyContributionAdmin(admin.ModelAdmin):
    list_display = ('worker', 'month', 'year', 'calculated_salary', 'amount_due', 'payment_status')
    list_filter = ('payment_status', 'year', 'month')
    search_fields = ('worker__username', 'mpesa_transaction_id')
    readonly_fields = ('created_at', 'updated_at')

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
    
    # OPTIMIZATION: Add pagination and select_related
    list_per_page = 50
    list_select_related = ('user', 'plan')

    fieldsets = (
        (None, {'fields': ('user', 'plan', 'amount', 'payment_method')}),
        ('Transaction Details', {'fields': ('transaction_id', 'phone_number', 'payment_date')}),
        ('Status & Notes', {'fields': ('status', 'verification_notes', 'admin_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )