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
            'password', 'first_name', 'last_name', 'email', 'user_type',
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
            'first_name': '👤 First Name',
            'last_name': '👤 Last Name',
            'email': '📧 Email address',
            'phone_number': '📞 Phone number (+254...)',
            'bio': '📝 Your bio / about section',
            'county': '📍 County',
            'constituency': '📍 Constituency',
            'major_town': '🏘️ Current town / area / nearest place',
            'ward': '📍 Ward',
            'mpesa_code': '💳 M-Pesa confirmation code (if paid)',
            'police_clearance': '🛡️ Certificate of Good Conduct (PDF/Image)',
            'skills': '🛠️ e.g. Cooking, Laundry, Childcare',
            'experience': '💼 Describe your relevant experience...',
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
            # LOCK DOCUMENTS if already verified or awaiting review
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

        # Crispy layout for edit profile (Advanced & Elegant)
        self.helper = FormHelper()
        self.helper.form_tag = False
        layout_list = [
            Fieldset(
                'Personal Identity',
                Div(
                    Div('first_name', css_class='md:col-span-1'),
                    Div('last_name', css_class='md:col-span-1'),
                    Div('email', css_class='md:col-span-1'),
                    Div('phone_number', css_class='md:col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-x-6'
                ),
                'bio',
                'profile_picture',
                css_class='space-y-6'
            ),
            Fieldset(
                'Work Location',
                Div(
                    Div('county', css_class='md:col-span-1'),
                    Div('constituency', css_class='md:col-span-1'),
                    Div('major_town', css_class='md:col-span-1'),
                    Div('ward', css_class='md:col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-x-6'
                ),
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8'
            ),
        ]
        
        if 'skills' in self.fields:
            layout_list.append(Fieldset(
                'Skills & Professional History',
                'skills',
                'experience',
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8'
            ))
            
        if 'id_document' in self.fields:
            layout_list.append(Fieldset(
                'Validation Documents',
                Div(
                    HTML("""
                        {% if user.documents_verified %}
                            <div class="mb-4 p-4 bg-green-50 border border-green-200 text-green-800 rounded-2xl text-xs flex items-center gap-3">
                                <span class="bg-green-500 text-white rounded-full p-1"><svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg></span>
                                <div><strong>Documents Verified:</strong> Your profile is fully unlocked and trustworthy.</div>
                            </div>
                        {% elif user.id_document or user.agreement_form or user.police_clearance %}
                            <div class="mb-4 p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-2xl text-xs flex items-center gap-3">
                                <span class="bg-amber-500 text-white rounded-full p-1 animate-pulse"><svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" fill="none"></path></svg></span>
                                <div><strong>Under Review:</strong> Our team is validating your documents.</div>
                            </div>
                        {% endif %}
                    """),
                ),
                'id_document',
                'agreement_form',
                'police_clearance',
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8'
            ))
            
        if 'is_verified' in self.fields:
            layout_list.append(Fieldset(
                'System Administration',
                Div(
                    Div('is_verified', css_class='md:col-span-1'),
                    Div('mpesa_code', css_class='md:col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-x-6'
                ),
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8 bg-slate-50 p-6 rounded-3xl'
            ))
            
        self.helper.layout = Layout(*layout_list)