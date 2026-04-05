from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'city', 'salary', 'posting_fee_paid', 'mpesa_code', 'is_active', 'created_at']
    list_filter = ['posting_fee_paid', 'city', 'job_type', 'is_active', 'is_featured']
    search_fields = ['title', 'description', 'requirements', 'employer__username']
    list_per_page = 20
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('employer', 'title', 'description', 'responsibilities', 'requirements')
        }),
        ('Compensation & Location', {
            'fields': ('salary', 'city', 'location', 'job_type', 'experience_level')
        }),
        ('Status & Payment', {
            'fields': ('is_active', 'is_featured', 'featured_until', 'posting_fee_paid', 'mpesa_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'created_at']
    list_filter = ['status', 'job__city', 'job__job_type']
    search_fields = ['job__title', 'applicant__username', 'cover_letter']
    list_per_page = 20
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('job', 'applicant', 'status')
        }),
        ('Application Details', {
            'fields': ('cover_letter', 'resume', 'experience', 'availability', 'preferred_hours', 'additional_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )