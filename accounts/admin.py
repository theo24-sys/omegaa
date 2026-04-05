from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from notifications.utils import create_notification


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'user_type', 'is_verified', 'documents_verified', 'view_documents_link', 'phone_number', 'county')
    list_filter = ('user_type', 'is_verified', 'documents_verified', 'date_joined')
    actions = ['approve_documents', 'deny_documents']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('user_type', 'bio', 'phone_number', 'county', 'constituency', 'major_town', 'ward', 'profile_picture')}),
        ('Worker Documents', {
            'fields': (
                'id_document', 'id_document_preview',
                'agreement_form', 'agreement_form_preview',
                'police_clearance', 'police_clearance_preview',
                'documents_verified', 'documents_verified_at'
            ),
            'description': 'Review documents below before verifying.',
        }),
        ('Verification & Badges', {
            'fields': (
                'is_verified', 'mpesa_code',
                'badge_verified_id', 'badge_cleaning', 'badge_childcare',
                'badge_elder_care', 'badge_kitchen', 'badge_professional_standards', 'badge_appliance'
            )
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    readonly_fields = [
        'id_document_preview', 'agreement_form_preview', 'police_clearance_preview', 'documents_verified_at'
    ]

    def id_document_preview(self, obj):
        if obj.id_document:
            return format_html('<a href="{}" target="_blank">View ID Document</a>', obj.id_document.url)
        return "No document uploaded"

    def agreement_form_preview(self, obj):
        if obj.agreement_form:
            return format_html('<a href="{}" target="_blank">View Agreement Form</a>', obj.agreement_form.url)
        return "No document uploaded"

    def police_clearance_preview(self, obj):
        if obj.police_clearance:
            return format_html('<a href="{}" target="_blank">View Police Clearance</a>', obj.police_clearance.url)
        return "No document uploaded"

    def view_documents_link(self, obj):
        if obj.user_type == 'househelp' and (obj.id_document or obj.agreement_form or obj.police_clearance):
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                               '#059669' if obj.documents_verified else '#d97706',
                               'Verified' if obj.documents_verified else 'Review Pending')
        return "-"
    view_documents_link.short_description = 'Doc Status'

    def approve_documents(self, request, queryset):
        count = 0
        for user in queryset.filter(user_type='househelp'):
            user.documents_verified = True
            user.documents_verified_at = timezone.now()
            user.save()
            create_notification(
                recipient=user,
                notification_type='system',
                title='Documents Approved!',
                message='Your identity documents have been verified. You can now apply for jobs!'
            )
            count += 1
        self.message_user(request, f"{count} workers have been verified and notified.")
    approve_documents.short_description = "Approve and notify selected workers"

    def deny_documents(self, request, queryset):
        count = 0
        for user in queryset.filter(user_type='househelp'):
            user.documents_verified = False
            user.save()
            create_notification(
                recipient=user,
                notification_type='system',
                title='Documents Denied',
                message='Your uploaded documents were not accepted. Please ensure they are clear and valid, then re-upload in your profile settings.'
            )
            count += 1
        self.message_user(request, f"{count} workers have been denied and notified.")
    deny_documents.short_description = "Deny and notify selected workers"

    def save_model(self, request, obj, form, change):
        if change and 'documents_verified' in form.changed_data and form.cleaned_data.get('documents_verified'):
            obj.documents_verified_at = timezone.now()
        super().save_model(request, obj, form, change)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2')}
        ),
    )
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-date_joined',)


admin.site.register(CustomUser, CustomUserAdmin)