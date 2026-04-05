# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, HTML
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'user_type',
            'county', 'constituency', 'major_town', 'ward',
            'phone_number', 'bio', 'profile_picture',
            'password1', 'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove 'username' field entirely from this form to prevent silent validation failures
        # since we are manually setting username to phone_number in save().
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields.pop('username')

        # Common Tailwind classes for all fields
        common_classes = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'

        # Placeholders
        placeholders = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'yourname@example.com',
            'phone_number': '+2547xxxxxxxx',
            'bio': 'Tell us a bit about yourself or your experience...',
            'county': 'Select your County',
            'constituency': 'Select Constituency',
            'major_town': 'Current town / area / nearest place (e.g. Rongai, Syokimau)',
            'ward': 'Your Ward',
        }

        for field_name, field in self.fields.items():
            # Apply Tailwind classes
            field.widget.attrs.update({'class': common_classes})

            # Add placeholders where defined
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

            # Enforce requirements for explicit fields
            if field_name in ['first_name', 'last_name', 'phone_number']:
                field.required = True

            # Make certain fields optional
            if field_name in ['bio', 'profile_picture']:
                field.required = False

        # Optional: Crispy layout (if you want more control than just |crispy in template)
        self.helper = FormHelper()
        self.helper.form_tag = False  # We'll use <form> in template
        self.helper.layout = Layout(
            Fieldset(
                'Account Information',
                Div('first_name', css_class='md:col-span-1'),
                Div('last_name', css_class='md:col-span-1'),
                Div('email', css_class='md:col-span-1'),
                Div('phone_number', css_class='md:col-span-1'),
                Div('password1', css_class='md:col-span-1'),
                Div('password2', css_class='md:col-span-1'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6'
            ),
            Fieldset(
                'Profile Details',
                Div('user_type', css_class='md:col-span-1'),
                'bio',
                'profile_picture',
                css_class='space-y-6 border-t border-pink-200 pt-6'
            ),
            Fieldset(
                'Location (helps with job matching)',
                Div('county', css_class='md:col-span-1'),
                Div('constituency', css_class='md:col-span-1'),
                Div('ward', css_class='md:col-span-1'),
                Div('major_town', css_class='md:col-span-1'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-pink-200 pt-6'
            ),
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('phone_number')
        if commit:
            user.save()
        return user



class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            'username', 'password', 'first_name', 'last_name', 'email', 'user_type',
            'county', 'constituency', 'major_town', 'ward',
            'phone_number', 'bio', 'profile_picture',
            'skills', 'experience',
            'id_document', 'agreement_form',
            'is_verified', 'mpesa_code',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # No longer popping password - Admin needs it!
        # It won't show in frontend anyway because it's not in the crispy Layout.

        # Common Tailwind classes
        common_classes = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'

        # Placeholders (same as signup + admin fields)
        placeholders = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email address',
            'phone_number': 'Phone number (+254...)',
            'bio': 'Your bio / about section',
            'county': 'County',
            'constituency': 'Constituency',
            'major_town': 'Current town / area / nearest place',
            'ward': 'Ward',
            'mpesa_code': 'M-Pesa confirmation code (if paid)',
            'police_clearance': 'Certificate of Good Conduct (PDF/Image)',
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': common_classes})
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

            # Make most fields optional
            if field_name not in ['first_name', 'last_name', 'email', 'county', 'constituency', 'major_town', 'ward']:
                field.required = False

        # Hide document/skills/experience for non-househelps; hide admin fields for non-staff
        instance = kwargs.get('instance')
        
        if instance and instance.user_type != 'househelp':
            for f in ('skills', 'experience', 'id_document', 'agreement_form', 'police_clearance', 'badge_appliance'):
                self.fields.pop(f, None)
        elif instance and instance.user_type == 'househelp':
            # Add placeholders for househelp-only fields
            if 'skills' in self.fields:
                self.fields['skills'].widget.attrs['placeholder'] = 'e.g. Cooking, Laundry, Childcare'
            if 'experience' in self.fields:
                self.fields['experience'].widget.attrs['placeholder'] = 'Describe your relevant experience...'
            
            # LOCK DOCUMENTS if already verified or awaiting review
            # Awaiting review = (doc exists) AND (not verified)
            is_awaiting_review = (instance.id_document or instance.agreement_form or instance.police_clearance) and not instance.documents_verified
            if instance.documents_verified or is_awaiting_review:
                for f in ('id_document', 'agreement_form', 'police_clearance'):
                    if f in self.fields:
                        self.fields[f].disabled = True
                        if is_awaiting_review:
                            self.fields[f].help_text = "Verification in progress. Documents are locked."
                        else:
                            self.fields[f].help_text = "Documents verified and locked."

        if instance and not instance.is_staff:
            for f in ('is_verified', 'mpesa_code'):
                self.fields.pop(f, None)

        # Crispy layout for edit profile (better organization)
        self.helper = FormHelper()
        self.helper.form_tag = False
        layout_list = [
            Fieldset(
                'Basic Information',
                Div('first_name', css_class='md:col-span-1'),
                Div('last_name', css_class='md:col-span-1'),
                Div('email', css_class='md:col-span-1'),
                Div('user_type', css_class='md:col-span-1'),
                Div('phone_number', css_class='md:col-span-1'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6'
            ),
            Fieldset(
                'Location Information',
                Div('county', css_class='md:col-span-1'),
                Div('constituency', css_class='md:col-span-1'),
                Div('major_town', css_class='md:col-span-1'),
                Div('ward', css_class='md:col-span-1'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-pink-200 pt-6'
            ),
            Fieldset(
                'Additional Details',
                'bio',
                'profile_picture',
                css_class='space-y-6 border-t border-pink-200 pt-6'
            ),
        ]
        if 'skills' in self.fields:
            layout_list.append(Fieldset(
                'Skills & Experience (househelp)',
                'skills',
                'experience',
                css_class='space-y-6 border-t border-pink-200 pt-6'
            ))
        if 'id_document' in self.fields:
            layout_list.append(Fieldset(
                'Documents (required for job applications)',
                Div(
                    HTML("""
                        {% if user.documents_verified %}
                            <div class="mb-4 p-4 bg-green-50 border border-green-200 text-green-800 rounded-xl text-sm flex items-center gap-2">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                                <strong>Documents Verified:</strong> Your profile is fully unlocked.
                            </div>
                        {% elif user.id_document or user.agreement_form or user.police_clearance %}
                            <div class="mb-4 p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-sm flex items-center gap-2">
                                <svg class="w-5 h-5 animate-pulse" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                                <strong>Under Review:</strong> Admin is currently reviewing your documents.
                            </div>
                        {% endif %}
                    """),
                ),
                'id_document',
                'agreement_form',
                'police_clearance',
                css_class='space-y-6 border-t border-pink-200 pt-6'
            ))
        if 'is_verified' in self.fields:
            layout_list.append(Fieldset(
                'Admin / Verification (only visible to staff)',
                Div('is_verified', css_class='md:col-span-1'),
                Div('mpesa_code', css_class='md:col-span-1'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-pink-200 pt-6'
            ))
        self.helper.layout = Layout(*layout_list)