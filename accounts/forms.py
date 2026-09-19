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
            'first_name', 'last_name', 'email', 'user_type',
            'county', 'constituency', 'major_town', 'ward',
            'phone_number', 'bio', 'profile_picture',
            'skills', 'experience',
            'agreement_form',
            'is_verified', 'mpesa_code',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # No longer popping password - Admin needs it!
        # It won't show in frontend anyway because it's not in the crispy Layout.

        # Common Tailwind classes
        common_classes = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'

        # Placeholders (plain text, matching the friendly labels below)
        placeholders = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'you@example.com',
            'phone_number': 'e.g. 0712 345 678',
            'bio': 'Tell employers a bit about yourself...',
            'county': 'County',
            'constituency': 'Constituency',
            'major_town': 'Town / area (e.g. Rongai, Syokimau)',
            'ward': 'Ward',
            'mpesa_code': 'e.g. SLK7XYZ99',
            'skills': 'e.g. Cooking, Laundry, Childcare',
            'experience': 'Describe your work experience...',
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': common_classes})
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

            # Make most fields optional
            if field_name not in ['first_name', 'last_name', 'email', 'county', 'constituency', 'major_town', 'ward']:
                field.required = False

        # Friendly, plain-English labels and help texts
        friendly = {
            'first_name': ('First Name', None),
            'last_name': ('Last Name', None),
            'email': ('Email Address', None),
            'phone_number': ('Phone Number', 'Use the mobile number employers can reach you on.'),
            'bio': ('About You', 'Tell employers a little about yourself and your experience.'),
            'profile_picture': ('Profile Photo', 'A clear, smiling photo of your face helps you get hired faster.'),
            'county': ('County', None),
            'constituency': ('Constituency', None),
            'major_town': ('Town / Area', None),
            'ward': ('Ward', None),
            'skills': ('Skills', 'List your skills separated by commas, e.g. Cooking, Laundry, Childcare.'),
            'experience': ('Work Experience', 'Describe any relevant jobs or experience you have.'),
            'agreement_form': ('Signed Worker Agreement', 'Upload the agreement you signed during registration (PDF or image).'),
            'id_document': ('National ID / Passport', 'Upload a clear photo or scan of your ID.'),
            'police_clearance': ('Police Clearance (Good Conduct)', 'Upload your valid Good Conduct certificate.'),
        }
        for fname, (label, help_text) in friendly.items():
            if fname in self.fields:
                self.fields[fname].label = label
                if help_text:
                    self.fields[fname].help_text = help_text

        # Plain FileInput: never shows raw storage paths like "Currently: profile_pics/xxx.jpg".
        if 'profile_picture' in self.fields:
            self.fields['profile_picture'].widget = forms.FileInput(attrs={
                'accept': 'image/*',
            })
        for doc_field in ('agreement_form', 'id_document', 'police_clearance'):
            if doc_field in self.fields:
                self.fields[doc_field].widget = forms.FileInput(attrs={
                    'accept': '.pdf,image/*',
                })

        # Hide document/skills/experience for non-househelps; hide admin fields for non-staff
        instance = kwargs.get('instance')
        
        if instance and instance.user_type != 'househelp':
            for f in ('skills', 'experience', 'id_document', 'agreement_form', 'police_clearance', 'badge_appliance'):
                if f in self.fields: self.fields.pop(f)
        elif instance and instance.user_type == 'househelp':
            # LOCK DOCUMENTS if already verified or awaiting review
            is_awaiting_review = (instance.agreement_form) and not instance.documents_verified
            if instance.documents_verified or is_awaiting_review:
                for f in ('agreement_form',):
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
                'About You',
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
                'Where You Work',
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
                'Skills & Experience',
                'skills',
                'experience',
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8'
            ))
            
        if 'agreement_form' in self.fields:
            # Build the document status banner in Python (crispy HTML() blocks do
            # NOT process {% if %} template tags, which used to leak raw tags).
            instance = kwargs.get('instance')
            if instance is not None and getattr(instance, 'documents_verified', False):
                status_html = (
                    '<div class="mb-4 p-4 bg-green-50 border border-green-200 text-green-800 '
                    'rounded-2xl text-xs"><strong>✔ Verified:</strong> your documents have been '
                    'checked and approved. You can now apply for jobs.</div>'
                )
            elif instance is not None and getattr(instance, 'agreement_form', None):
                status_html = (
                    '<div class="mb-4 p-4 bg-amber-50 border border-amber-200 text-amber-800 '
                    'rounded-2xl text-xs"><strong>⏳ Under review:</strong> our team is checking '
                    'your documents. This usually takes a short while.</div>'
                )
            else:
                status_html = (
                    '<div class="mb-4 p-4 bg-blue-50 border border-blue-200 text-blue-800 '
                    'rounded-2xl text-xs"><strong>📄 Action needed:</strong> upload your signed '
                    'worker agreement below to unlock job applications.</div>'
                )
            layout_list.append(Fieldset(
                'Verification Documents',
                Div(HTML(status_html)),
                'agreement_form',
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8'
            ))
            
        if 'is_verified' in self.fields:
            layout_list.append(Fieldset(
                'Admin Controls',
                Div(
                    Div('is_verified', css_class='md:col-span-1'),
                    Div('mpesa_code', css_class='md:col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-x-6'
                ),
                css_class='space-y-6 border-t border-pink-100 pt-8 mt-8 bg-slate-50 p-6 rounded-3xl'
            ))
            
        self.helper.layout = Layout(*layout_list)